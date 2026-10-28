// Exercise the frontend's mode behavior without a browser or extra dependencies.
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

function frontend() {
  const elements = new Map();
  class Element {
    constructor() {
      this.value = ''; this.dataset = {}; this.style = {}; this.children = [];
      this.parts = new Map(); this.listeners = {}; this.textContent = '';
      this.classList = { add() {}, remove() {}, toggle() {} };
    }
    set id(value) { elements.set(value, this); }
    addEventListener(event, handler) { this.listeners[event] = handler; }
    append(child) { this.children.push(child); }
    add(child) { this.append(child); }
    replaceChildren(...children) { this.children = children; this.value = children[0]?.value || ''; }
    querySelector(selector) {
      if (!this.parts.has(selector)) this.parts.set(selector, new Element());
      return this.parts.get(selector);
    }
    setAttribute() {}
  }
  const document = {
    getElementById(id) {
      if (!elements.has(id)) elements.set(id, new Element());
      return elements.get(id);
    },
    createElement() { return new Element(); }
  };
  document.getElementById('mode').value = '4';
  const handlers = {}, emitted = [];
  const socket = {
    connected: true,
    on(event, handler) { handlers[event] = handler; },
    timeout() { return this; },
    emit(...args) { emitted.push(args); }
  };
  let now = 0;
  const context = vm.createContext({
    document, window: { BUGHOUSE_CONFIG: { backendUrl: 'http://localhost:5000' } },
    sessionStorage: { getItem() { return null; }, setItem() {} },
    io() { return socket; }, performance: { now: () => now }, setInterval() {},
    Option: function(text, value) { this.text = text; this.value = value; }
  });
  vm.runInContext(fs.readFileSync(path.join(__dirname, '../frontend/assets/app.js'), 'utf8'), context);
  const run = (code) => vm.runInContext(code, context);
  function snapshot(mode) {
    const squares = Array.from({ length: 8 }, () => Array(8).fill(null));
    squares[6].fill('P'); squares[1].fill('p');
    return { mode, required_players: mode, player_count: mode, status: 'playing',
      clocks_paused: false, rematch_votes: [], players: {}, result: null,
      clocks: { a_white:180000, a_black:180000, b_white:180000, b_black:180000 },
      boards: { a:{ squares:structuredClone(squares),turn:'white' },
                b:{ squares:structuredClone(squares),turn:'white' } } };
  }
  return { document, handlers, emitted, run, snapshot, advance(ms) { now += ms; } };
}

test('solo can select the active color on both boards and paused clocks stay frozen', () => {
  const ui = frontend(), state = ui.snapshot(1);
  ui.handlers.state(state);
  ui.run("acceptSeat({seat:'a_white', seats:['a_white','a_black','b_white','b_black'], token:'test'})");
  assert.equal(ui.document.getElementById('testing-controls').hidden, false);
  assert.equal(ui.run("canMove('a') && canMove('b')"), true);
  ui.run("choose('a', 'e2')");
  assert.equal(ui.run("legalTargets('a', 'e2').includes('e4')"), true);
  state.boards.a.turn = 'black';
  ui.handlers.state(state);
  ui.run("choose('a', 'e7')");
  assert.equal(ui.run("legalTargets('a', 'e7').includes('e5')"), true);
  state.clocks_paused = true;
  ui.handlers.state(state);
  ui.advance(30000);
  ui.run('drawClocks()');
  assert.equal(ui.document.getElementById('clock-a_black').textContent, '3:00');
  assert.equal(ui.document.getElementById('clock-toggle').textContent, 'Resume clocks');
  ui.document.getElementById('clock-toggle').listeners.click();
  assert.equal(ui.emitted.at(-1)[0], 'set_clock_paused');
  assert.equal(ui.emitted.at(-1)[1].paused, false);
});

test('two-player frontend only enables its team on the appropriate turns', () => {
  const ui = frontend(), state = ui.snapshot(2);
  ui.handlers.state(state);
  ui.run("acceptSeat({seat:'a_white', seats:['a_white','b_black'], token:'test'})");
  assert.equal(ui.run("canMove('a')"), true);
  assert.equal(ui.run("canMove('b')"), false);
  assert.equal(ui.document.getElementById('testing-controls').hidden, true);
  state.boards.b.turn = 'black';
  ui.handlers.state(state);
  assert.equal(ui.run("canMove('b')"), true);
  assert.equal(ui.run("legalTargets('b', 'e7').includes('e5')"), true);
});

test('four-player frontend controls only one side and spectators cannot move', () => {
  const ui = frontend();
  ui.handlers.state(ui.snapshot(4));
  assert.equal(ui.run("canMove('a') || canMove('b')"), false);
  ui.run("acceptSeat({seat:'a_white', seats:['a_white'], token:'test'})");
  assert.equal(ui.run("canMove('a')"), true);
  assert.equal(ui.run("canMove('b')"), false);
  assert.equal(ui.document.getElementById('testing-controls').hidden, true);
});
