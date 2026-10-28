import unittest

from game import Game, SEATS


class GameTests(unittest.TestCase):
    def setUp(self):
        self.time = 1000.0
        self.game = Game(now=lambda: self.time)
        self.tokens = {}
        for seat in SEATS:
            _, self.tokens[seat] = self.game.join(seat, name=seat, requested=seat)

    def test_starting_positions_and_four_clocks(self):
        state = self.game.snapshot()
        self.assertEqual(state["status"], "playing")
        self.assertEqual(state["clocks"], dict.fromkeys(SEATS, 180000))
        for board in state["boards"].values():
            self.assertEqual(sum(piece is not None for row in board["squares"] for piece in row), 32)
            self.assertEqual(board["squares"][0], list("rnbqkbnr"))

    def test_independent_turns_and_increments(self):
        self.time += 5
        self.game.move("a_white", "a", "e2", "e4")
        self.assertEqual(self.game.boards["a"]["turn"], "black")
        self.assertEqual(self.game.boards["b"]["turn"], "white")
        self.assertEqual(self.game.remaining["a_white"], 177)
        self.assertEqual(self.game.remaining["b_white"], 175)
        self.time += 3
        self.game.move("b_white", "b", "d2", "d3")
        self.assertEqual(self.game.remaining["a_black"], 177)
        self.assertEqual(self.game.remaining["a_white"], 177)
        self.assertEqual(self.game.remaining["b_white"], 174)
        self.assertEqual(self.game.remaining["b_black"], 180)

    def test_illegal_moves_do_not_change_turn_or_award_increment(self):
        for sid, board, origin, target in [
            ("a_black", "a", "e7", "e5"), ("spectator", "a", "e2", "e4"),
            ("a_white", "b", "e2", "e4"), ("a_white", "a", "b1", "c3"),
            ("a_white", "a", "e2", "d3"), ("a_white", "a", "e2", "e5"),
            ("a_white", "a", "e2", "e1"), ("a_white", "a", "z9", "a3"),
            ("a_white", "a", None, "e4"), ("a_white", "a", [1, 2], "e4"),
        ]:
            with self.subTest(origin=origin, target=target), self.assertRaises(ValueError):
                self.game.move(sid, board, origin, target)
        self.assertEqual(self.game.remaining["a_white"], 180)
        self.assertEqual(self.game.boards["a"]["turn"], "white")

    def test_blocked_pawns_and_no_captures(self):
        self.game.boards["a"]["squares"][5][4] = "p"
        for target in ("e3", "e4"):
            with self.assertRaises(ValueError):
                self.game.move("a_white", "a", "e2", target)
        self.game.boards["a"]["squares"][5][4] = None
        self.game.move("a_white", "a", "e2", "e4")
        self.game.move("a_black", "a", "a7", "a6")
        with self.assertRaises(ValueError):
            self.game.move("a_white", "a", "e4", "e6")

    def test_first_timeout_stops_both_boards_at_exact_flag(self):
        self.game.remaining["a_white"] = 1
        self.game.remaining["b_white"] = 2
        self.time += 10
        state = self.game.snapshot()
        self.assertEqual(state["result"]["winner"], 2)
        self.assertEqual(state["clocks"]["a_white"], 0)
        self.assertEqual(state["clocks"]["b_white"], 1000)
        self.time += 20
        self.assertEqual(self.game.snapshot()["clocks"]["b_white"], 1000)
        with self.assertRaises(ValueError):
            self.game.move("a_white", "a", "a2", "a3")

    def test_simultaneous_opposing_flags_draw(self):
        self.time += 180
        self.assertIsNone(self.game.snapshot()["result"]["winner"])

    def test_reconnect_and_seat_ownership(self):
        self.game.disconnect("a_white")
        self.time += 3
        seat, _ = self.game.join("new-sid", self.tokens["a_white"])
        self.assertEqual(seat, "a_white")
        self.assertEqual(self.game.remaining["a_white"], 177)
        with self.assertRaises(ValueError):
            self.game.join("intruder", self.tokens["a_white"])
        with self.assertRaises(ValueError):
            self.game.move("a_white", "a", "a2", "a3")
        self.game.move("new-sid", "a", "a2", "a3")

    def test_waiting_clocks_and_disconnected_lobby_seat(self):
        game = Game(now=lambda: self.time)
        game.join("one", requested="a_white")
        self.time += 100
        self.assertEqual(game.snapshot()["clocks"]["a_white"], 180000)
        game.disconnect("one")
        self.assertEqual(game.players, {})

    def test_four_votes_reset_boards_and_clocks(self):
        self.game.move("a_white", "a", "a2", "a4")
        self.time += 180
        self.game.advance()
        for seat in SEATS[:3]:
            self.game.rematch(seat)
        self.assertEqual(self.game.status, "finished")
        self.game.rematch(SEATS[3])
        self.assertEqual(self.game.status, "playing")
        self.assertEqual(self.game.boards["a"]["squares"][6][0], "P")
        self.assertEqual(self.game.remaining, dict.fromkeys(SEATS, 180))


if __name__ == "__main__":
    unittest.main()
