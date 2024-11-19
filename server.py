from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# Define the path to your video file
VIDEO_FILE_PATH = "path/to/your/video.mp4"

@app.route('/')
def index():
    """Serve the main HTML page."""
    return render_template("index.html")

@socketio.on("offer")
def handle_offer(data):
    """Handle offer from client and send back answer."""
    emit("offer", data, broadcast=True)

@socketio.on("answer")
def handle_answer(data):
    """Handle answer from client and send back to offerer."""
    emit("answer", data, broadcast=True)

@socketio.on("ice-candidate")
def handle_ice_candidate(data):
    """Handle ICE candidates."""
    emit("ice-candidate", data, broadcast=True)

@socketio.on("volume")
def handle_volume(data):
    """Handle volume data from client."""
    print(f"Microphone Volume: {data['volume']}")

if __name__ == '__main__':
    socketio.run(app, debug=True)
