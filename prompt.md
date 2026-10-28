Initial prompt:
Build the Phase 1 MVP of a four-player Bughouse Chess game (you can check the spec)
Use HTML/CSS/JavaScript for the frontend and Python Flask + Flask-SocketIO for the backend.
Implement two standard chessboards with all pieces in their starting positions. Four players should be able to join from separate browsers, each controlling one color on one board.
For now, implement only basic pawn movement (one or two squares forward), independent turn management on both boards, real-time synchronization across all four players, and four synchronized 3+2 chess clocks.
Keep the backend authoritative for game state and clock timing. Do not implement captures, other piece movements, or checkmate yet.



Second prompt:
The frontend and backend should be completely separated, with the frontend hosted on GitHub Pages and the backend hosted on Render.com. Flask should not serve frontend files.
Make the changes now.
Also, along the way, write a doc.md file (which is equivalent to a readme file)



Third prompt:
Game Modes:
   1-Player Mode: One player controls all four sides on both boards, mainly for testing. (testing only)
   2-Player Mode: Each player controls one team (two sides on separate boards).
   4-Player Mode: Each player controls one side, which is the standard multiplayer mode.
   All three modes use the same game rules and backend logic.
   Chess clocks can be paused in 1-Playerfor testing.
Make the following changes