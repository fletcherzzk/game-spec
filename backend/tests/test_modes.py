import unittest

from game import Game, SEATS


class ModeTests(unittest.TestCase):
    def setUp(self):
        self.time = 1000.0
        self.game = Game(now=lambda: self.time)

    def test_solo_controls_all_sides_with_normal_turns_and_increments(self):
        self.game.join('solo', mode=1)
        self.assertEqual(self.game.seats_for_sid('solo'), list(SEATS))
        self.assertEqual(self.game.status, 'playing')
        for board in ('a', 'b'):
            with self.assertRaises(ValueError):
                self.game.move('solo', board, 'e7', 'e5')
            self.game.move('solo', board, 'e2', 'e4')
            self.game.move('solo', board, 'e7', 'e5')
        self.assertEqual(self.game.remaining, dict.fromkeys(SEATS, 182))
        with self.assertRaises(ValueError):
            self.game.move('spectator', 'a', 'd2', 'd4')

    def test_two_players_control_opposite_teams(self):
        self.game.join('team1', requested='a_white', mode=2)
        self.assertEqual(self.game.status, 'waiting')
        self.assertEqual(set(self.game.seats_for_sid('team1')), {'a_white', 'b_black'})
        self.time += 20
        self.assertEqual(self.game.snapshot()['clocks']['a_white'], 180000)
        self.game.join('team2', requested='b_white', mode=2)
        self.assertEqual(self.game.status, 'playing')
        with self.assertRaises(ValueError):
            self.game.move('team1', 'b', 'e2', 'e4')
        self.game.move('team1', 'a', 'e2', 'e4')
        self.game.move('team2', 'b', 'e2', 'e4')
        self.game.move('team2', 'a', 'e7', 'e5')
        self.game.move('team1', 'b', 'e7', 'e5')
        self.assertEqual(self.game.snapshot()['player_count'], 2)

    def test_mode_is_atomic_and_locked_when_lobby_has_players(self):
        with self.assertRaises(ValueError):
            self.game.join('invalid', requested='bad', mode=1)
        self.assertEqual(self.game.mode, 4)
        self.game.join('first', mode=2)
        with self.assertRaises(ValueError):
            self.game.join('second', mode=4)
        self.assertEqual(len(self.game.players), 2)
        self.game.disconnect('first')
        self.assertEqual(self.game.players, {})
        self.game.join('new', mode=1)
        self.assertEqual(self.game.mode, 1)

    def test_invalid_modes_are_rejected(self):
        for mode in (0, 3, '1', True, [], {}):
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                self.game.join('test', mode=mode)
        self.assertEqual(self.game.players, {})

    def test_pause_resume_is_authoritative_and_moves_still_work(self):
        self.game.join('solo', mode=1)
        self.time += 5
        self.game.set_clock_paused('solo', True)
        self.assertEqual(self.game.remaining['a_white'], 175)
        self.time += 1000
        self.game.move('solo', 'a', 'e2', 'e4')
        self.assertEqual(self.game.remaining['a_white'], 177)
        self.assertEqual(self.game.remaining['b_white'], 175)
        self.assertEqual(self.game.remaining['a_black'], 180)
        self.game.set_clock_paused('solo', False)
        self.time += 3
        snapshot = self.game.snapshot()
        self.assertEqual(snapshot['clocks']['a_black'], 177000)
        self.assertEqual(snapshot['clocks']['b_white'], 172000)
        self.assertEqual(snapshot['clocks']['a_white'], 177000)

    def test_pause_permissions_and_timeout_cannot_be_evaded(self):
        self.game.join('solo', mode=1)
        with self.assertRaises(ValueError):
            self.game.set_clock_paused('spectator', True)
        with self.assertRaises(ValueError):
            self.game.set_clock_paused('solo', 'true')
        self.time += 180
        with self.assertRaises(ValueError):
            self.game.set_clock_paused('solo', True)
        self.assertEqual(self.game.status, 'finished')
        for mode in (2, 4):
            game = Game(now=lambda: self.time)
            for index in range(mode):
                game.join(str(index), mode=mode)
            with self.assertRaises(ValueError):
                game.set_clock_paused('0', True)

    def test_reconnect_restores_entire_group_and_keeps_pause_state(self):
        for mode in (1, 2):
            with self.subTest(mode=mode):
                game = Game(now=lambda: self.time)
                _, token = game.join('original', mode=mode)
                if mode == 2:
                    game.join('other', mode=2)
                else:
                    game.set_clock_paused('original', True)
                original = game.seats_for_sid('original')
                game.disconnect('original')
                self.assertEqual(game.seats_for_sid('original'), [])
                game.join('restored', token=token)
                self.assertEqual(game.seats_for_sid('restored'), original)
                self.assertEqual(game.clocks_paused, mode == 1)
                self.assertTrue(all(game.players[s]['sid'] == 'restored' for s in original))
                with self.assertRaises(ValueError):
                    game.join('intruder', token=token)

    def test_rematch_needs_one_vote_per_controller(self):
        for mode in (1, 2, 4):
            with self.subTest(mode=mode):
                game = Game(now=lambda: self.time)
                for index in range(mode):
                    game.join(str(index), mode=mode)
                self.time += 180
                game.advance()
                for index in range(mode - 1):
                    game.rematch(str(index))
                    game.rematch(str(index))
                    self.assertEqual(game.status, 'finished')
                game.rematch(str(mode - 1))
                self.assertEqual(game.status, 'playing')
                self.assertFalse(game.clocks_paused)
                self.assertEqual(game.mode, mode)
                self.assertEqual(game.remaining, dict.fromkeys(SEATS, 180))
