# game-spec
game spec for 15114 homework



Game Name: Bughouse Chess

Bughouse Chess is a chess variant played by four players with two teams of two players on two separate chessboards. Each team has one player playing White and one playing Black.

The main difference from traditional chess is that when a player captures an opponent's piece, the captured piece is transferred to their teammate, who can place it on their own board instead of making a normal move. After being placed on the board, a chess piece move like normal chess move, but no promotion permitted for pawns. 

Both chess games take place simultaneously. The first team to checkmate an opponent or win on time wins the entire match.

The game is fun because it combines traditional chess strategy with teamwork, resource management, and fast-paced decision-making. Players must coordinate with teammates to obtain useful pieces while defending their own kings.



The full intended feature set:

A. Chess board: Standard chess board with row and column labels

B. Chess moves: Standard chess movement and capture rules: 
    Note: include castling, en passant, and but do not include pawn promotion.
    Only exceptions: 1. Promotion of pawns is not allowed 
                       (The pawn just disappears when promotion in normal check should happen) 
                     2. When a player capture an opponent piece, it will be transferred to the teammate
                     3. Placement of pieces should be counted as a move

C. Special Placement Rules for placing chess pieces:
   1. Pieces may only be placed on empty squares
   2. Pieces cannot be placed on row ranks 1, 2, 7, or 8. 
   3. Placing a piece cannot directly put the opponent's king in check.
   4. A placement must not leave the player's own king in check.
   5. Each placement consumes one piece from the player's reserve.

D. Game Rules check: 
   1. Checkmate:  
      Should have a checkmake Detection, accounting for possible defensive piece placements.
      The match ends immediately when either board reaches checkmate.
   2. Chess clock timming:
      Each player starts with 3 minutes, with a 2-second increment after every move
      (with placement of pieces counted as a move)
      If any player's clock reaches zero, their team loses the match.
    

E. Interface: 
   1. Two chessboards displayed side by side: 
      A player should be able to see the game of the teammate (this is important)
   2. Should have a bank for piece available to be placed on the board for each player
   3. Should use mouse-based movement and piece placement
   4. Visual indicators showing whose turn it is on each board.
   5. Four visible chess clocks

   Game Modes:
   1-Player Mode: One player controls all four sides on both boards, mainly for testing. (testing only)
   2-Player Mode: Each player controls one team (two sides on separate boards).
   4-Player Mode: Each player controls one side, which is the standard multiplayer mode.
   All three modes use the same game rules and backend logic.
   Chess clocks can be paused in 1-Playerfor testing.

F. Backend: (important)
   The game should support four players playing simultaneously from separate browsers.
   The backend should maintain the shared game state, including both chessboards, captured-piece reserves, player turns, and chess clocks.
   The backend should communicate with all four players to synchronize moves, piece transfers, and game-ending events in real time.
   (The backend does not need to store previously played games, it just restart after the game ends)




Acceptance criteria:
1. Two Boards: Two 8×8 chessboards are displayed with standard starting positions.
2. Four players can play in two teams, with one White and one Black player per team. Multiplayer Synchronization: Four players can connect to the same game session from separate browsers. Moves, captures, piece placements, and game-ending events are synchronized across all four players.
3. Piece Movement: Players can select and move chess pieces according to the rules
4. Capturing and piece transfer should work
5. Piece placement: Players can select an available reserve piece and place it onto a legal
   empty square instead of making a normal move. 
6. Checkmate and check validation should work
7. Chess clock should work





Priorities: If time does not allow:
Ignore the rules: 
   1. Pieces cannot be placed on row ranks 1, 2, 7, or 8. 
   2. Placing a piece cannot directly put the opponent's king in check.
   3. Special Chess Moves: Castling, en passant

If implementation difficulties are encountered, supporting only the 2-Player Mode for actual gameplay is acceptable. 





      







