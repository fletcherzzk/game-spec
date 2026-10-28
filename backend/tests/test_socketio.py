import unittest

import app as server
from game import Game, SEATS


class MultiplayerTests(unittest.TestCase):
    def setUp(self):
        self.time = 1000.0
        server.game = Game(now=lambda: self.time)
        # These tests drive time explicitly rather than using the background worker.
        server.worker_started = True
        self.clients = [server.socketio.test_client(server.app) for _ in range(5)]

    def tearDown(self):
        for client in self.clients:
            if client.is_connected():
                client.disconnect()

    def latest(self, client):
        return [event["args"][0] for event in client.get_received() if event["name"] == "state"][-1]

    def test_four_clients_receive_moves_and_authoritative_clocks(self):
        for client, seat in zip(self.clients, SEATS):
            reply = client.emit("join", {"seat": seat, "name": seat}, callback=True)
            self.assertTrue(reply["ok"])
        self.time += 5
        reply = self.clients[0].emit("move", {"board": "a", "from": "e2", "to": "e4", "elapsed": 0}, callback=True)
        self.assertTrue(reply["ok"])
        for client in self.clients:
            state = self.latest(client)
            self.assertEqual(state["boards"]["a"]["squares"][4][4], "P")
            self.assertEqual(state["boards"]["a"]["turn"], "black")
            self.assertEqual(state["boards"]["b"]["turn"], "white")
            self.assertEqual(state["clocks"]["a_white"], 177000)
            self.assertEqual(state["clocks"]["b_white"], 175000)
        self.assertFalse(self.clients[4].emit("move", {"board": "b", "from": "e2", "to": "e4"}, callback=True)["ok"])
        self.assertFalse(self.clients[4].emit("join", {}, callback=True)["ok"])

    def test_malformed_events_and_private_tokens(self):
        client = self.clients[0]
        for payload in (None, [], {"name": []}, {"seat": {}}, {"token": "é" * 64}):
            self.assertFalse(client.emit("join", payload, callback=True)["ok"])
        reply = client.emit("join", {}, callback=True)
        self.assertTrue(reply["ok"])
        state = self.latest(client)
        self.assertNotIn("token", state["players"][reply["seat"]])
        self.assertNotIn("sid", state["players"][reply["seat"]])
        for payload in (None, [], {"board": []}, {"board": "a", "from": {}, "to": None}):
            self.assertFalse(client.emit("move", payload, callback=True)["ok"])

    def test_backend_health_and_no_frontend_routes(self):
        client = server.app.test_client()
        self.assertEqual(client.get('/health').json['status'], 'ok')
        self.assertIsNone(server.app.static_folder)
        for path in ("/", "/index.html", "/static/app.js", "/assets/style.css", "/frontend/index.html"):
            with self.subTest(path=path):
                response = client.get(path)
                self.assertEqual(response.status_code, 404)
                response.close()

    def test_socketio_cross_origin_handshake(self):
        client = server.app.test_client()
        allowed = server.app.config['FRONTEND_ORIGINS'][0]
        response = client.get('/socket.io/?EIO=4&transport=polling', headers={'Origin': allowed})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Access-Control-Allow-Origin'], allowed)
        self.assertNotIn('Access-Control-Allow-Credentials', response.headers)
        response.close()
        response = client.get('/socket.io/?EIO=4&transport=polling', headers={'Origin': 'https://untrusted.invalid'})
        self.assertEqual(response.status_code, 400)
        self.assertNotIn('Access-Control-Allow-Origin', response.headers)
        response.close()

    def test_origin_configuration(self):
        self.assertEqual(server.allowed_origins('https://example.github.io/, http://localhost:8000'),
                         ['https://example.github.io', 'http://localhost:8000'])
        for value in ('*', '', 'https://example.github.io/repo/', 'https://example.com?x=1'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                server.allowed_origins(value)

    def test_solo_assignments_and_pause_are_broadcast_to_spectators(self):
        reply = self.clients[0].emit('join', {'mode': 1}, callback=True)
        self.assertTrue(reply['ok'])
        self.assertEqual(set(reply['seats']), set(SEATS))
        self.time += 5
        reply = self.clients[0].emit('set_clock_paused', {'paused': True}, callback=True)
        self.assertTrue(reply['ok'])
        self.time += 500
        self.assertTrue(self.clients[0].emit('move', {'board': 'b', 'from': 'd2', 'to': 'd4'}, callback=True)['ok'])
        for client in self.clients:
            state = self.latest(client)
            self.assertEqual(state['mode'], 1)
            self.assertEqual(state['player_count'], 1)
            self.assertTrue(state['clocks_paused'])
            self.assertEqual(state['clocks']['b_white'], 177000)
        self.assertFalse(self.clients[1].emit('set_clock_paused', {'paused': False}, callback=True)['ok'])
        for payload in (None, {}, {'paused': 'true'}, {'paused': 1}):
            self.assertFalse(self.clients[0].emit('set_clock_paused', payload, callback=True)['ok'])

    def test_two_player_team_assignment_and_pause_rejected(self):
        first = self.clients[0].emit('join', {'mode': 2, 'seat': 'a_white'}, callback=True)
        second = self.clients[1].emit('join', {'mode': 2, 'seat': 'a_black'}, callback=True)
        self.assertEqual(set(first['seats']), {'a_white', 'b_black'})
        self.assertEqual(set(second['seats']), {'a_black', 'b_white'})
        self.assertFalse(self.clients[0].emit('set_clock_paused', {'paused': True}, callback=True)['ok'])
        self.assertFalse(self.clients[0].emit('move', {'board': 'b', 'from': 'e2', 'to': 'e4'}, callback=True)['ok'])
        self.assertTrue(self.clients[1].emit('move', {'board': 'b', 'from': 'e2', 'to': 'e4'}, callback=True)['ok'])


if __name__ == "__main__":
    unittest.main()
