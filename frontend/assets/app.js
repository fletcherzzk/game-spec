/* State is read-only here. The server approves every move and owns all clocks. */
const $ = (id) => document.getElementById(id);
const pieces = { K:'♚', Q:'♛', R:'♜', B:'♝', N:'♞', P:'♟', k:'♚', q:'♛', r:'♜', b:'♝', n:'♞', p:'♟' };
const pieceNames = {k:'king',q:'queen',r:'rook',b:'bishop',n:'knight',p:'pawn'};
const seatNames = {a_white:'A · White',a_black:'A · Black',b_white:'B · White',b_black:'B · Black'};
const teamFor = (seat) => ['a_white','b_black'].includes(seat) ? 1 : 2;
let state = null, receivedAt = 0, mySeat = null, mySeats = [], selection = null, pending = false;
let token = null;
try { token = sessionStorage.getItem('bughouse-token'); } catch (_) {}
const backendUrl = window.BUGHOUSE_CONFIG?.backendUrl?.trim();
// Cross-origin Socket.IO connects only to the explicitly configured backend.
const socket = io(backendUrl || undefined, {
  autoConnect: Boolean(backendUrl),
  withCredentials: false
});
function notice(message = '') { $('notice').textContent = message; }
socket.on('connect', () => {
  $('connection').textContent = 'Live connection';
  $('connection-dot').classList.add('online');
  if (token) socket.emit('join', {token}, (reply) => {
    if (reply.ok) acceptSeat(reply);
    else { token = null; mySeat = null; mySeats = []; try { sessionStorage.removeItem('bughouse-token'); } catch (_) {} notice(reply.error); render(); }
  });
  render();
});
socket.on('disconnect', () => {
  $('connection').textContent = 'Reconnecting…';
  $('connection-dot').classList.remove('online');
  selection = null;
  pending = false;
  notice('Connection lost. Reconnecting automatically; the server retains the clock state.');
  render();
});
socket.on('connect_error', () => {
  $('connection').textContent = 'Backend unavailable';
  $('connection-dot').classList.remove('online');
  notice('Cannot reach the game server. Check the backend URL and allowed frontend origin. Retrying automatically.');
});
socket.on('state', (next) => {
  state = next;
  receivedAt = performance.now();
  if (selection && (!canMove(selection.board) || pieceAt(selection.board, selection.square) !== ownPawn(selection.board))) selection = null;
  render();
});
function acceptSeat(reply) {
  mySeat = reply.seat; mySeats = reply.seats; token = reply.token;
  try { sessionStorage.setItem('bughouse-token', token); } catch (_) {}
  notice(); render();
}
$('join-form').addEventListener('submit', (event) => {
  event.preventDefault();
  if (!socket.connected) return notice('Wait for the connection to return.');
  $('join-button').disabled = true;
  socket.timeout(5000).emit('join', {name:$('name').value, seat:$('seat').value || null, mode:Number($('mode').value)}, (error, reply) => {
    if (error) notice('No response yet. Try joining again.');
    else if (reply.ok) acceptSeat(reply);
    else notice(reply.error);
    render();
  });
});
function ownPawn(board) { return state.boards[board].turn === 'white' ? 'P' : 'p'; }
function canMove(board) { return socket.connected && state?.status === 'playing' && mySeats.includes(`${board}_${state.boards[board].turn}`); }
function pieceAt(board, square) { return state.boards[board].squares[8 - Number(square[1])][square.charCodeAt(0)-97]; }
function legalTargets(board, square) {
  if (!canMove(board) || pieceAt(board, square) !== ownPawn(board)) return [];
  const white = state.boards[board].turn === 'white', rank = Number(square[1]), step = white ? 1 : -1;
  const targets = [];
  for (let distance = 1; distance <= ((rank === (white ? 2 : 7)) ? 2 : 1); distance++) {
    const next = rank + step * distance;
    if (next < 1 || next > 8 || pieceAt(board, square[0]+next)) break;
    targets.push(square[0]+next);
  }
  return targets;
}
function choose(board, square) {
  if (pending || !canMove(board)) return;
  if (selection?.board === board && legalTargets(board, selection.square).includes(square)) {
    const origin = selection.square;
    pending = true; selection = null; notice(); render();
    socket.timeout(5000).emit('move', {board, from:origin, to:square}, (error, reply) => {
      pending = false;
      if (error) notice('Move response delayed. Check the board before trying again.');
      else if (!reply.ok) notice(reply.error);
      render();
    });
  } else {
    selection = pieceAt(board, square) === ownPawn(board) && !(selection?.board === board && selection.square === square) ? {board,square} : null;
    render();
  }
}
// Build squares once so keyboard focus survives the four state updates per second.
const cells = {};
for (const board of ['a','b']) {
  cells[board] = {};
  for (let rank = 8; rank >= 1; rank--) for (const file of 'abcdefgh') {
    const square = file+rank, button = document.createElement('button');
    button.type = 'button'; button.className = 'square';
    button.addEventListener('click', () => choose(board, square));
    button.innerHTML = '<span class="piece"></span><span class="coord rank"></span><span class="coord file"></span>';
    cells[board][square] = button;
    $('board-'+board).append(button);
  }
}
function renderPlayer(board, color, position) {
  const seat = `${board}_${color}`, player = state.players[seat], team = teamFor(seat);
  const container = $(`player-${board}-${position}`);
  if (container.dataset.seat !== seat) {
    container.dataset.seat = seat;
    container.innerHTML = '<div class="player-info"><div class="avatar"></div><div><div class="player-name"></div><div class="player-meta"></div></div></div><div class="clock"></div>';
  }
  container.querySelector('.avatar').textContent = color === 'white' ? '♙' : '♟';
  container.querySelector('.player-name').textContent = (player?.name || 'Open seat') + (mySeats.includes(seat) ? ' (you)' : '');
  const meta = container.querySelector('.player-meta');
  meta.textContent = `TEAM ${team} · ${color === 'white' ? 'White' : 'Black'}${player && !player.connected ? ' · Offline' : ''}`;
  meta.className = `player-meta team-${team}`;
  container.querySelector('.clock').id = `clock-${seat}`;
}
function render() {
  if (!state) return;
  const playing = state.status === 'playing', finished = state.status === 'finished';
  $('lobby').hidden = Boolean(mySeat) || state.status !== 'waiting';
  $('identity').hidden = !mySeat;
  if (mySeat) $('identity').textContent = state.mode === 1 ? '1-Player testing · You control all four sides' :
    `${state.mode}-Player mode · Team ${teamFor(mySeat)} · You control ${mySeats.map(s => seatNames[s]).join(' + ')}`;
  $('mode').disabled = state.player_count > 0;
  if (state.player_count > 0) $('mode').value = String(state.mode);
  const selectedMode = Number($('mode').value);
  $('lobby-help').textContent = state.player_count > 0 ? `${state.mode}-Player mode locked · Both boards start when ${state.required_players} player${state.required_players === 1 ? '' : 's'} join.` :
    selectedMode === 1 ? 'Testing only: control all sides and optionally pause the clocks.' :
    selectedMode === 2 ? 'Each player controls one team across both boards.' : 'Each player controls one side. The first player locks the mode.';
  const oldSeat = $('seat').value;
  $('seat').replaceChildren(new Option(selectedMode === 2 ? 'First available team' : 'First available seat',''));
  const choices = selectedMode === 1 ? {a_white:'All four sides (testing)'} : selectedMode === 2 ?
    {a_white:'Team 1 · A White + B Black', a_black:'Team 2 · A Black + B White'} :
    Object.fromEntries(Object.entries(seatNames).map(([seat,label]) => [seat, `${label} · Team ${teamFor(seat)}`]));
  for (const [seat, label] of Object.entries(choices)) {
    const option = new Option(`${label}${state.players[seat] ? ' (taken)' : ''}`, seat);
    option.disabled = Boolean(state.players[seat]); $('seat').add(option);
  }
  if (oldSeat && oldSeat in choices && !state.players[oldSeat]) $('seat').value = oldSeat;
  $('join-button').disabled = !socket.connected || Object.keys(state.players).length === 4;
  $('match-status').textContent = playing ? `${state.mode}-Player · ${state.clocks_paused ? 'Clocks paused · Testing' : 'Match live'}` : finished ?
    (state.result.winner ? `Team ${state.result.winner} wins on time` : 'Draw · Simultaneous timeouts') : `${state.player_count} / ${state.required_players} players · Waiting to start`;
  $('testing-controls').hidden = state.mode !== 1 || !mySeat || !playing;
  $('clock-toggle').disabled = !socket.connected;
  $('clock-toggle').textContent = state.clocks_paused ? 'Resume clocks' : 'Pause clocks';
  $('rematch').hidden = !finished || !mySeat;
  $('rematch').disabled = !socket.connected || state.rematch_votes.includes(mySeat);
  $('rematch').textContent = `Rematch · ${state.rematch_votes.length}/${state.required_players} votes`;
  for (const board of ['a','b']) {
    // Orient both boards from the player's team's perspective.
    const controlled = mySeats.filter(s => s.startsWith(board+'_'));
    const flipped = state.mode === 1 ? false : controlled.length ? controlled[0].endsWith('black') :
      mySeat ? mySeat.endsWith('white') : false;
    $('card-'+board).classList.toggle('yours', controlled.length > 0);
    $('turn-'+board).textContent = finished ? 'Match finished' : `${state.boards[board].turn === 'white' ? 'White' : 'Black'} to move${canMove(board) ? ' · Your turn' : ''}`;
    renderPlayer(board, flipped ? 'white' : 'black', 'top');
    renderPlayer(board, flipped ? 'black' : 'white', 'bottom');
    const targets = selection?.board === board ? legalTargets(board, selection.square) : [];
    for (const [square, cell] of Object.entries(cells[board])) {
      const file = square.charCodeAt(0)-97, rank = Number(square[1]);
      const visualRow = flipped ? rank-1 : 8-rank, visualCol = flipped ? 7-file : file;
      cell.style.gridRow = visualRow+1; cell.style.gridColumn = visualCol+1;
      const piece = pieceAt(board, square), last = state.boards[board].last_move;
      cell.className = 'square' + ((file+rank)%2 === 1 ? ' dark' : '') +
        (last && [last.from,last.to].includes(square) ? ' last' : '') +
        (selection?.board === board && selection.square === square ? ' selected' : '') +
        (targets.includes(square) ? ' legal' : '');
      const glyph = cell.querySelector('.piece');
      glyph.textContent = pieces[piece] || '';
      glyph.className = 'piece ' + (piece && piece === piece.toUpperCase() ? 'white' : 'black');
      cell.querySelector('.rank').textContent = visualCol === 0 ? rank : '';
      cell.querySelector('.file').textContent = visualRow === 7 ? square[0] : '';
      cell.setAttribute('aria-label', `${square}${piece ? ` ${piece === piece.toUpperCase() ? 'white' : 'black'} ${pieceNames[piece.toLowerCase()]}` : ' empty'}${targets.includes(square) ? ', legal destination' : ''}`);
      cell.setAttribute('aria-pressed', String(selection?.board === board && selection.square === square));
    }
  }
  drawClocks();
}
function drawClocks() {
  if (!state) return;
  const elapsed = Math.max(0, performance.now() - receivedAt);
  for (const seat of Object.keys(seatNames)) {
    const active = state.status === 'playing' && !state.clocks_paused && state.boards[seat[0]].turn === seat.split('_')[1];
    // Freeze the last estimate offline. Only server snapshots determine a timeout.
    const ms = Math.max(0, state.clocks[seat] - (active && socket.connected ? elapsed : 0));
    const seconds = Math.ceil(ms/1000), clock = $('clock-'+seat);
    if (!clock) continue;
    clock.textContent = `${Math.floor(seconds/60)}:${String(seconds%60).padStart(2,'0')}`;
    clock.className = `clock${active ? ' active' : ''}${ms < 20000 ? ' low' : ''}`;
    clock.setAttribute('aria-label', `${seatNames[seat]} clock: ${clock.textContent}`);
  }
}
setInterval(drawClocks, 100);
$('mode').addEventListener('change', () => { $('seat').value = ''; render(); });
$('clock-toggle').addEventListener('click', () => {
  if (!socket.connected || !state) return;
  socket.timeout(5000).emit('set_clock_paused', {paused: !state.clocks_paused}, (error, reply) => {
    if (error) notice('Clock response delayed. Check the clock status before trying again.');
    else if (!reply.ok) notice(reply.error);
    else notice();
  });
});
$('rematch').addEventListener('click', () => socket.timeout(5000).emit('rematch', (error, reply) => {
  if (error) notice('Rematch response delayed. Try again.');
  else if (!reply.ok) notice(reply.error);
}));
if (!backendUrl) {
  $('connection').textContent = 'Backend URL required';
  $('join-button').disabled = true;
  notice('Set the BACKEND_URL GitHub repository variable and deploy Pages, or configure frontend/config.js.');
}
