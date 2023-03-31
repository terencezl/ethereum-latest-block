import eventlet
eventlet.monkey_patch()
import argparse
from flask import Flask, request
from flask.templating import render_template
from flask_socketio import SocketIO, emit
from loguru import logger
from block_utils import check_latest_block, get_latest_block

# this is a global variable to store the latest block
# no matter how many clients are connected, fetch once
global_payload = None

def global_ticker():
    global global_payload
    last_bn = -1
    while True:
        latest_bn = check_latest_block()
        if latest_bn > last_bn:
            logger.info(f"New block [{latest_bn}] found.")
            global_payload = get_latest_block(latest_bn)
            last_bn = global_payload["bn"]
        else:
            eventlet.sleep(1)


app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
session_ids = set()


@app.route("/")
def index():
    return render_template("index.html")


@socketio.on("connect")
def handle_connect():
    session_id = request.sid
    session_ids.add(session_id)
    logger.info(f"Client [{session_id}] connected.")


@socketio.on("disconnect")
def handle_disconnect():
    session_id = request.sid
    session_ids.remove(session_id)
    logger.info(f"Client [{session_id}] disconnected.")


@socketio.on("get_latest_block")
def handle_get_latest_block():
    session_id = request.sid
    logger.info(f"Client [{session_id}] requested latest block.")

    last_bn = -1
    while True:
        if session_id not in session_ids:
            logger.info(f"Client [{session_id}] already disconnected. Stopping loop.")
            break

        if global_payload is None:
            eventlet.sleep(1)
            continue

        latest_bn = global_payload["bn"]
        if latest_bn > last_bn:
            logger.info(f"Sending to client [{session_id}] new block [{latest_bn}].")
            emit("latest_block", global_payload)
            last_bn = latest_bn
        else:
            eventlet.sleep(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="localhost")
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args()

    # start the global ticker
    eventlet.spawn(global_ticker)

    socketio.run(app, host=args.host, port=args.port)
