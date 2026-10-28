# Bughouse Chess - Phase 1

# Basic information (manually written here)

What is achieved so far:
One, two, or four players, two boards, pawn-only moves, independent turns, and authoritative 3+2 clocks. 
The static frontend and the Flask-SocketIO backend.Solo testing mode.
Controls all four sides and supports pausing clocks; two-player mode assigns one team per player.

Note: I have got an AI written Readme: See doc.md 


Current Tech stack:
Frontend : HTML, CSS, JavaScript
           Frontend Hosting: GitHub Pages

Backend: Python, Flask, Flask-SocketIO
         Backend Hosting: Render.com

Note: Flask does not serve frontend files,
      The frontend and backend is completely separated
      (be remindful of this in testing)








## Install and run on another machine (written by AI)

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





## Controls and player information (Mostly manually written)

-Join: Select a game mode, enter your name, choose a seat/team, and click Join match.

1-Player Mode: Control all four sides for testing. Clocks can be paused or resumed.

2-Player Mode: Each player controls one team (one side on each board).

4-Player Mode: Each player controls one side on one board.

Movement: Click a pawn and then a highlighted square to move. Only basic pawn movement is currently supported.

Turns: Both boards operate independently, with White moving first.

Clocks: Each player has 3 minutes with a 2-second increment per valid move. A timeout ends the match.

Multiplayer: Moves and clocks are synchronized across all players. Spectators can watch.

Rematch: All players must agree to restart a match. Game data is stored in memory and resets when the backend restarts.



## Acceptance criteria status()

Phase 1 MVP is implemented, including all three game modes. Full Bughouse Chess is still under development.

Two Chessboards: Complete.

Four-Player Multiplayer: Partial — pawn moves and clocks synchronized.

Chess Piece Movement: Partial — pawns only.

Capturing and Piece Transfer: Not implemented at all

Reserve Piece Placement: Not implemented at all

Check and Checkmate: Not implemented at all

Chess Clocks (3+2): Complete.

Additional Features: 1-Player, 2-Player, and 4-Player modes are implemented.

See SPEC.md for full requirements.

## Code Map: Where to Change Behavior

1. **`backend/game.py`:** Core game logic, shared state, player assignments, movement rules, and clocks.
2. **`Game.move()`:** Pawn movement, turn validation, and board updates. Add future chess rules here.
3. **`Game.advance()`, `set_clock_paused()`:** Clock countdowns, timeout detection, and pause controls.
4. **`Game.join()`, `rematch()`, `snapshot()`:** Player connections, rematches, and synchronized game state.
5. **`backend/app.py`:** Flask server, Socket.IO events, input validation, and real-time synchronization.
6. **`frontend/index.html`:** Chessboards, lobby, game modes, and controls.
7. **`frontend/assets/style.css`:** Interface styling, board layout, and piece highlights.
8. **`frontend/assets/app.js`:** Player interactions, piece selection, rendering, and server communication.
9. **`frontend/config.js`:** Backend connection URL.
10. **`frontend/assets/vendor/socket.io.min.js`:** Socket.IO browser client library.
11. **`backend/requirements.txt`:** Python dependencies.
12. **`render.yaml`:** Render backend deployment configuration.
13. **`.github/workflows/pages.yml`:** GitHub Pages frontend deployment.
14. **`backend/tests/`:** Backend rules, multiplayer, clock, and integration tests.
15. **`tests/frontend.test.cjs`:** Frontend behavior tests.
16. **`spec.md`:** Full game specification and acceptance criteria.
17. **`README.md`, `doc.md`, `note.md`:** Project overview, documentation, and development notes.



## No bugs known now


## I cut the corner by having a MVP and basic frame work.




## What I'd Do Next (Priority Order)

Chess Movement: Implement legal moves for all pieces, including captures.
Piece Transfer: Transfer captured pieces to the teammate's reserve.
Piece Placement: Allow players to place reserve pieces on legal squares.
Check and Checkmate: Implement check validation and game-ending conditions.
Special Rules: Add castling, en passant, and custom placement restrictions.
Testing and Polish: Test all three game modes, fix bugs, and improve the interface.


