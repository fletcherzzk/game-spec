"""Authoritative Phase 1 game rules. All times use a monotonic clock."""
import math
import secrets
import time

SEATS = ("a_white", "a_black", "b_white", "b_black")
TEAMS = {"a_white": 1, "b_black": 1, "a_black": 2, "b_white": 2}
INITIAL_SECONDS = 180.0
INCREMENT = 2.0


def starting_board():
    return [list("rnbqkbnr"), list("pppppppp"), *[[None] * 8 for _ in range(4)],
            list("PPPPPPPP"), list("RNBQKBNR")]


class Game:
    def __init__(self, now=time.monotonic):
        self.now = now
        self.players = {}
        self.rematch_votes = set()
        self.reset()

    def reset(self):
        self.boards = {key: {"squares": starting_board(), "turn": "white",
                             "last_move": None, "moves": 0} for key in ("a", "b")}
        self.remaining = {seat: INITIAL_SECONDS for seat in SEATS}
        self.status = "waiting"
        self.result = None
        self.updated_at = self.now()
        self.rematch_votes.clear()

    def advance(self):
        now = self.now()
        elapsed = max(0, now - self.updated_at)
        if self.status == "playing":
            active = [f"{board}_{data['turn']}" for board, data in self.boards.items()]
            expired = [seat for seat in active if self.remaining[seat] <= elapsed]
            # Stop both boards at the first actual flag, even if the worker woke late.
            charged = min([elapsed] + [self.remaining[seat] for seat in expired])
            for seat in active:
                self.remaining[seat] = max(0.0, self.remaining[seat] - charged)
            if expired:
                flags = [seat for seat in active if self.remaining[seat] <= 0]
                losers = {TEAMS[seat] for seat in flags}
                winner = (3 - next(iter(losers))) if len(losers) == 1 else None
                self.status = "finished"
                self.result = {"reason": "timeout", "flagged": flags, "winner": winner}
        self.updated_at = now

    def seat_for_sid(self, sid):
        return next((s for s, p in self.players.items() if p["sid"] == sid), None)

    def join(self, sid, token=None, name="Player", requested=None):
        self.advance()
        existing = next((s for s, p in self.players.items()
                         if token and secrets.compare_digest(p["token"], token)), None)
        if existing:
            player = self.players[existing]
            if player["sid"] and player["sid"] != sid:
                raise ValueError("This seat is already connected in another window.")
            player["sid"] = sid
            return existing, player["token"]
        if self.seat_for_sid(sid):
            raise ValueError("You already have a seat.")
        if self.status != "waiting":
            raise ValueError("The match has started. You can watch or reconnect to your seat.")
        seat = requested or next((s for s in SEATS if s not in self.players), None)
        if seat not in SEATS or seat in self.players:
            raise ValueError("That seat is unavailable.")
        token = secrets.token_hex(32)
        self.players[seat] = {"name": name.strip()[:24] or "Player", "token": token, "sid": sid}
        if len(self.players) == 4 and all(p["sid"] for p in self.players.values()):
            self.status = "playing"
            self.updated_at = self.now()
        return seat, token

    def disconnect(self, sid):
        self.advance()
        seat = self.seat_for_sid(sid)
        if seat:
            if self.status == "waiting":
                del self.players[seat]
            else:
                self.players[seat]["sid"] = None
                self.rematch_votes.discard(seat)

    def move(self, sid, board, origin, target):
        self.advance()
        if self.status != "playing":
            raise ValueError("The match is not running.")
        seat = self.seat_for_sid(sid)
        if board not in self.boards or seat != f"{board}_{self.boards[board]['turn']}":
            raise ValueError("You can only move on your board during your turn.")
        if not all(isinstance(s, str) and len(s) == 2 and s[0] in "abcdefgh"
                   and s[1] in "12345678" for s in (origin, target)):
            raise ValueError("Invalid square.")
        col, row = ord(origin[0]) - 97, 8 - int(origin[1])
        end_col, end_row = ord(target[0]) - 97, 8 - int(target[1])
        data = self.boards[board]
        squares = data["squares"]
        white = data["turn"] == "white"
        direction, start = (-1, 6) if white else (1, 1)
        distance = (end_row - row) * direction
        if squares[row][col] != ("P" if white else "p"):
            raise ValueError("Phase 1 supports pawn moves only.")
        if col != end_col or distance not in (1, 2) or (distance == 2 and row != start):
            raise ValueError("Move a pawn one square forward, or two from its starting rank.")
        if any(squares[row + direction * step][col] is not None
               for step in range(1, distance + 1)):
            raise ValueError("Pawns cannot jump over or capture pieces in Phase 1.")
        squares[end_row][end_col], squares[row][col] = squares[row][col], None
        self.remaining[seat] += INCREMENT
        data["turn"] = "black" if white else "white"
        data["last_move"] = {"from": origin, "to": target}
        data["moves"] += 1

    def rematch(self, sid):
        self.advance()
        seat = self.seat_for_sid(sid)
        if self.status != "finished" or seat is None:
            raise ValueError("Only seated players can request a rematch after the match ends.")
        self.rematch_votes.add(seat)
        if len(self.rematch_votes) == 4 and all(p["sid"] for p in self.players.values()):
            self.reset()
            self.status = "playing"

    def snapshot(self):
        self.advance()
        return {"status": self.status, "boards": self.boards,
                "clocks": {s: math.ceil(t * 1000) for s, t in self.remaining.items()},
                "players": {s: {"name": p["name"], "connected": p["sid"] is not None,
                                 "team": TEAMS[s]} for s, p in self.players.items()},
                "result": self.result, "rematch_votes": sorted(self.rematch_votes)}
