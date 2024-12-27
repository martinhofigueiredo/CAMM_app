from flask import Flask, render_template, send_from_directory
from flask_socketio import SocketIO, emit
import os
import tempfile
import numpy as np
from scipy.io.wavfile import write as write_wav
import torch
from tinyCLAP.tinyclap import CLAPBrain  # Adjusted import for submodule directory

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

VIDEO_DIRECTORY = "./videos"  # Default video directory

# Initialize the CLAP model (update hparams and other dependencies as needed)
hparams = {...}  # Load hparams configuration for CLAP
try:
    clap_model = CLAPBrain(modules=hparams['modules'], opt_class=None, hparams=hparams)
except Exception as e:
    print(f"Error loading CLAP model: {e}")
    clap_model = None

@app.route('/')
def index():
    """Serve the main HTML page."""
    return render_template("index.html")  # Updated HTML file name

@app.route('/videos/<path:filename>')
def serve_video(filename):
    """Serve video files from the directory."""
    return send_from_directory(VIDEO_DIRECTORY, filename)

@socketio.on("request-stream")
def handle_stream_request(data):
    """Handle stream requests from clients."""
    video_type = data.get("type", "dash")  # Client can specify 'dash' or 'hls'
    video_name = data.get("name", "example.mpd")  # Default DASH manifest file

    if video_type == "dash":
        stream_url = f"/videos/{video_name}"
        emit("stream-url", {"url": stream_url, "type": "dash"})
    elif video_type == "hls":
        hls_name = video_name.replace(".mpd", ".m3u8")  # Example conversion for HLS
        stream_url = f"/videos/{hls_name}"
        emit("stream-url", {"url": stream_url, "type": "hls"})
    else:
        emit("error", {"message": "Unsupported video type requested."})

@socketio.on("audio-clip")
def handle_audio_clip(data):
    """Process incoming audio clips."""
    audio_bytes = data.get("audio")
    if not audio_bytes:
        emit("error", {"message": "No audio data received"})
        return

    # Save the audio temporarily
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
        temp_audio_path = temp_audio.name
        audio_array = np.frombuffer(audio_bytes, dtype=np.uint8)  # Convert bytes to numpy array
        write_wav(temp_audio_path, 16000, audio_array)  # Save as 16kHz WAV

    # Run inference with tinyCLAP
    results = run_clap_inference(temp_audio_path)
    emit("inference-result", {"results": results})

    # Optionally, clean up the temporary file
    os.remove(temp_audio_path)

def run_clap_inference(audio_path):
    """Run zero-shot inference on the audio file using CLAP."""
    if clap_model is None:
        return {"similarity_scores": [0]}

    try:
        # Load the audio file into a tensor
        audio_signal = torch.tensor(np.load(audio_path))  # Replace with appropriate loader
        audio_embed = clap_model.preprocess(audio_signal.unsqueeze(0))

        # Compare against predefined textual descriptions
        text_features = clap_model.prepare_txt_features([
            "This is the sound of applause",
            "This is a quiet room"
        ])
        similarity = clap_model.compute_sim(audio_embed, text_features)
        return {"similarity_scores": similarity.tolist()}
    except Exception as e:
        print(f"Error during inference: {e}")
        return {"similarity_scores": [0]}

@socketio.on("volume")
def handle_volume(data):
    """Handle volume data from client."""
    print(f"Microphone Volume: {data['volume']}")

if __name__ == '__main__':
    if not os.path.exists(VIDEO_DIRECTORY):
        os.makedirs(VIDEO_DIRECTORY)
        print(f"Video directory created at {VIDEO_DIRECTORY}. Please add your video files.")

    socketio.run(app, debug=True)
