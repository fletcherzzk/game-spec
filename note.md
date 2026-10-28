# Bughouse Phase 1: quick handoff

## Install and run on another machine

Install **Python 3.10+** and use a modern browser. Download and extract this repository
(or clone it), then open a terminal in its root folder. An internet connection is
needed to install the Python dependencies. Node.js is needed only for JavaScript tests.

On Windows PowerShell, start the backend:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
.\.venv\Scripts\python.exe backend/app.py
```

In a second terminal in the same folder, start the separate frontend server:

```powershell
.\.venv\Scripts\python.exe -m http.server 8000 --directory frontend
```

On macOS/Linux, create the environment with `python3 -m venv .venv` and substitute
`.venv/bin/python` for `.\.venv\Scripts\python.exe` in the other commands.

Play at **http://localhost:8000**. Check the backend at
**http://localhost:5000/health**; its root URL intentionally returns 404.
Stop either server with Ctrl+C. Flask never serves frontend files.

For players on different computers, everyone must connect to the **same backend**.
For LAN hosting, set `frontend/config.js`'s `backendUrl` to the host's LAN URL
(for example `http://192.168.1.10:5000`) and set backend `FRONTEND_ORIGINS` to the
frontend origin (`http://192.168.1.10:8000`). Allow the two ports through the host's
firewall if necessary. See [doc.md](doc.md) for detailed configuration and the
GitHub Pages frontend / Render backend deployment steps. Deployment files are
provided; actual hosting URLs and account configuration must still be supplied.

## Controls and player information

- Choose a mode, enter a name, choose an available seat/team, and click **Join match**.
  The first successful join locks the mode. Both boards start when enough players join.
- **1-Player (testing):** control all four sides. **Pause clocks / Resume clocks**
  freezes/unfreezes all countdowns; moves and two-second increments still work.
- **2-Player:** control one team. Team 1 is A White + B Black; Team 2 is A Black + B White.
- **4-Player:** control one side on one board. Use independently opened tabs or
  separate browsers/profiles for multiple local players; duplicated tabs may copy a seat token.
- Click your pawn, then a highlighted destination. Pawns move one square forward,
  or two from their starting rank if the path is empty. No captures or other pieces move yet.
- White starts on each board; each board has its own turn. Turn labels and highlights
  show whose move it is. Both boards and all four clocks remain visible.
- Clocks are **3 minutes + 2 seconds per valid move**, controlled by the server.
  A flag ends the whole match; exactly simultaneous opposing flags draw.
- Reloading the same tab restores its seat. Disconnection does not automatically
  pause clocks. Spectators can watch without joining but cannot move or pause.
- After a timeout, every controller must vote for a rematch. Rematches keep the mode
  and restart clocks. Restart the backend for a fresh lobby or a different mode;
  all game state is in memory and is lost on restart.

## Acceptance criteria status

These numbers refer to the **full acceptance criteria in [spec.md](spec.md)**.
The requested Phase 1 subset and all three modes are implemented; full Bughouse is unfinished.

| # | Criterion | Status |
| --- | --- | --- |
| 1 | Two 8×8 boards with standard starting positions | **Met**, including all pieces and coordinate labels. |
| 2 | Four players, two teams, synchronized moves/captures/placements/endings | **Partial:** four-player assignments, pawn moves, turns, clocks, and timeout endings synchronize. Captures and placements are absent. |
| 3 | Legal piece selection and movement | **Partial:** forward pawn moves only; no other piece moves, captures, or check-based legality. |
| 4 | Capturing and piece transfer | **Not implemented.** |
| 5 | Reserve piece placement | **Not implemented**, including reserves and placement restrictions. |
| 6 | Check and checkmate validation | **Not implemented.** |
| 7 | Chess clocks | **Met for Phase 1:** four authoritative 3+2 clocks, independent turns, timeout results, and solo testing pause. Placement increments await placement support. |

Additional mode requirements are met: solo controls all sides, two players control
opposite teams, four players control individual sides, and all share one rules engine.

## Code map: where to change behavior

| File / class / major function | Responsibility |
| --- | --- |
| `backend/game.py` — `Game` | Shared authoritative state and rules for every mode; no UI or Flask dependencies. |
| `starting_board()`, `Game.reset()` | Starting positions, fresh clocks, turns, and match reset. `SEATS`, `TEAMS`, `INITIAL_SECONDS`, `INCREMENT`, `MODES` define assignments and defaults. |
| `Game.groups()`, `join()`, `disconnect()`, `seat_for_sid()`, `seats_for_sid()` | Mode ownership, lobby locking, seat assignment, reconnect tokens, and disconnect behavior. |
| `Game.move()` | Ownership/turn checks, pawn legality, board updates, turn switching, and increments. Add future movement/capture rules here. |
| `Game.advance()`, `set_clock_paused()` | Monotonic countdowns, timeout outcomes, and solo-only pause authorization. |
| `Game.rematch()`, `snapshot()` | Controller voting/reset and public state sent to browsers; snapshots omit private credentials. |
| `backend/app.py` — `allowed_origins()`, `health()` | Backend configuration, cross-origin allowlist, and JSON health endpoint. |
| `backend/app.py` — Socket.IO event handlers, `handle()` | Input validation and dispatch to `Game` under a lock; returns acknowledgments/errors. |
| `backend/app.py` — `broadcast()`, `ticker()`, `connect()` | Broadcast snapshots after actions and every 250 ms; initialize clients and start the update worker. |
| `frontend/index.html` | Static page structure: two boards, lobby, mode selector, pause/rematch controls. |
| `frontend/assets/style.css` | Colors, pieces, highlights, responsive layout, and control styling. |
| `frontend/assets/app.js` — socket handlers, `acceptSeat()` | Connection/reconnection, received snapshots, and local controller identity. |
| `canMove()`, `ownPawn()`, `pieceAt()`, `legalTargets()`, `choose()` | Selection, destination hints, and move requests. Backend validation remains authoritative. |
| `render()`, `renderPlayer()`, `drawClocks()`, `notice()` | Board orientation, players, mode/control visibility, clock display interpolation, and feedback. Form/button handlers send join, pause, and rematch requests. |
| `frontend/config.js` | Public backend connection URL; local default uses port 5000. |
| `frontend/assets/vendor/socket.io.min.js` | Bundled third-party Socket.IO browser client. |
| `backend/requirements.txt` | Python dependencies, including the production server for Linux. |
| `render.yaml` | Backend deployment: one instance, one Gunicorn worker, environment settings, health check. |
| `.github/workflows/pages.yml` | Injects GitHub's `BACKEND_URL` variable and deploys only `frontend/` to Pages. |
| `backend/tests/test_game.py`, `test_modes.py` | Rules, timing, ownership, mode assignments, pause/resume, and rematch tests. |
| `backend/tests/test_socketio.py`, `test_frontend.py` | Multiplayer events, origin checks, backend/frontend separation, and static HTML asset checks. |
| `tests/frontend.test.cjs` | Dependency-free frontend behavior tests for modes, control permissions, and paused clock displays. |
| `backend/tests/__init__.py`, `.gitignore` | Test package marker; excludes local environments and generated Python files. |
| `spec.md`, `README.md`, `doc.md`, `note.md` | Full target specification, entry-point summary, detailed operating guide, and this brief handoff. |

Optional checks from the repository root:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s backend/tests -t backend -v
node tests/frontend.test.cjs
```
