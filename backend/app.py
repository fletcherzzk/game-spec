import os
from threading import Lock
from urllib.parse import urlsplit

from flask import Flask, request
from flask_socketio import SocketIO

from game import Game

def allowed_origins(value):
    origins = []
    for entry in value.split(","):
        origin = entry.strip().rstrip("/")
        parsed = urlsplit(origin)
        if (parsed.scheme not in ("http", "https") or not parsed.netloc or
                parsed.path or parsed.query or parsed.fragment or parsed.username or parsed.password):
            raise ValueError("FRONTEND_ORIGINS must contain comma-separated HTTP(S) origins without paths.")
        origins.append(origin)
    return origins


# No template or static routes: frontend files are hosted independently.
app = Flask(__name__, static_folder=None)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", os.urandom(32))
app.config["FRONTEND_ORIGINS"] = allowed_origins(os.environ.get(
    "FRONTEND_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000"))
socketio = SocketIO(app, async_mode="threading",
                    cors_allowed_origins=app.config["FRONTEND_ORIGINS"], cors_credentials=False)
game = Game()
game_lock = Lock()
worker_lock = Lock()
worker_started = False


@app.get("/health")
def health():
    return {"status": "ok", "service": "bughouse-backend"}


def broadcast():
    # Called under game_lock, including clock advancement and serialization.
    socketio.emit("state", game.snapshot())


def ticker():
    while True:
        socketio.sleep(0.25)
        with game_lock:
            broadcast()


@socketio.on("connect")
def connect():
    global worker_started
    with worker_lock:
        if not worker_started:
            socketio.start_background_task(ticker)
            worker_started = True
    with game_lock:
        socketio.emit("state", game.snapshot(), to=request.sid)


def handle(action):
    with game_lock:
        try:
            result = action() or {}
        except ValueError as error:
            result = {"ok": False, "error": str(error)}
        broadcast()
        return {"ok": True, **result}


@socketio.on("join")
def join(payload):
    if not isinstance(payload, dict):
        return {"ok": False, "error": "Invalid join request."}
    token, name, seat = payload.get("token"), payload.get("name", "Player"), payload.get("seat")
    if not isinstance(name, str) or (token is not None and
            (not isinstance(token, str) or len(token) != 64 or
             any(c not in "0123456789abcdef" for c in token))) or (seat is not None and not isinstance(seat, str)):
        return {"ok": False, "error": "Invalid join request."}

    def action():
        assigned, credential = game.join(request.sid, token, name, seat, payload.get("mode"))
        return {"seat": assigned, "seats": game.seats_for_sid(request.sid), "token": credential}
    return handle(action)


@socketio.on("move")
def move(payload):
    if not isinstance(payload, dict) or not isinstance(payload.get("board"), str):
        return {"ok": False, "error": "Invalid move request."}
    return handle(lambda: game.move(request.sid, payload.get("board"), payload.get("from"), payload.get("to")))


@socketio.on("rematch")
def rematch():
    return handle(lambda: game.rematch(request.sid))


@socketio.on("set_clock_paused")
def set_clock_paused(payload):
    if not isinstance(payload, dict) or type(payload.get("paused")) is not bool:
        return {"ok": False, "error": "paused must be a boolean."}
    return handle(lambda: game.set_clock_paused(request.sid, payload["paused"]))


@socketio.on("disconnect")
def disconnect(reason=None):
    with game_lock:
        game.disconnect(request.sid)
        broadcast()


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)),
                 debug=False, allow_unsafe_werkzeug=True)
