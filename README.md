# Bughouse Chess - Phase 1

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
