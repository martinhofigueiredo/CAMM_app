#!/usr/bin/env python3

from flask import Flask, render_template, send_from_directory, jsonify
from flask_socketio import SocketIO, emit
import os
import tempfile
import subprocess
import numpy as np
from datetime import datetime
from scipy.io.wavfile import write as write_wav
import torch

def load_config():
    import tomli

    # Load configuration from config.toml
    CONFIG_PATH = "config.toml"
    try:
        with open(CONFIG_PATH, "rb") as f:
            config = tomli.load(f)
            return config
    except Exception as e:
        print(f"Error loading configuration file {CONFIG_PATH}: {e}")
        exit(1)


def process_videos():
    """Check for unprocessed MP4 files and create HLS playlists."""
    # Load the list of processed videos
    if os.path.exists(PROCESSED_VIDEOS_FILE):
        with open(PROCESSED_VIDEOS_FILE, "r") as f:
            processed_videos = set(f.read().splitlines())
    else:
        processed_videos = set()

    qualities = config["ffmpeg"]["qualities"]

    for filename in os.listdir(VIDEO_DIRECTORY):
        if filename.endswith(".mp4") and filename not in processed_videos:
            mp4_path = os.path.join(VIDEO_DIRECTORY, filename)
            base_name = os.path.splitext(filename)[0]
            output_dir = os.path.join(VIDEO_DIRECTORY, base_name)

            # Create output directory for HLS files
            os.makedirs(output_dir, exist_ok=True)

            master_playlist_path = os.path.join(output_dir, f"{base_name}_master.m3u8")
            variant_playlists = []

            for q in qualities:
                scaled_m3u8_path = os.path.join(output_dir, f"{base_name}_{q}.m3u8")
                command = [
                    "ffmpeg",
                    "-i",
                    mp4_path,
                    "-vf",
                    f"scale=-2:{q}",
                    "-codec:V",
                    config["ffmpeg"]["video_codec"],
                    "-codec:a",
                    config["ffmpeg"]["audio_codec"],
                    "-strict",
                    "experimental",
                    "-hls_time",
                    str(config["ffmpeg"]["hls_time"]),
                    "-hls_playlist_type",
                    config["ffmpeg"]["playlist_type"],
                    "-hls_segment_filename",
                    os.path.join(output_dir, f"{base_name}_{q}_%03d.ts"),
                    scaled_m3u8_path,
                ]
                subprocess.run(command, check=True)
                variant_playlists.append((scaled_m3u8_path, q))

            with open(master_playlist_path, "w") as master:
                master.write("#EXTM3U\n#EXT-X-VERSION:3\n")
                for playlist, q in variant_playlists:
                    master.write(f'#EXT-X-STREAM-INF:BANDWIDTH={q*1000},RESOLUTION=1280x{q}\n')
                    master.write(f'{os.path.basename(playlist)}\n')

            processed_videos.add(filename)

    # Save the updated list of processed videos
    with open(PROCESSED_VIDEOS_FILE, "w") as f:
        f.write("\n".join(processed_videos))


def manage_audio_clips():
    """Ensure the number of audio clips does not exceed the maximum limit."""
    clips = sorted(
        (
            os.path.join(AUDIO_CLIP_DIRECTORY, f)
            for f in os.listdir(AUDIO_CLIP_DIRECTORY)
            if f.endswith(".wav")
        ),
        key=os.path.getmtime,
    )

    while len(clips) > MAX_CLIPS:
        oldest_clip = clips.pop(0)
        try:
            os.remove(oldest_clip)
            print(f"Removed old audio clip: {oldest_clip}")
        except OSError as e:
            print(f"Error removing audio clip {oldest_clip}: {e}")


def evaluate_msclap(audio_files):
    """
    This is an example using CLAP for zero-shot inference.
    """
    from msclap import CLAP
    import torch.nn.functional as F

    # Define classes for zero-shot
    # Should be in lower case and can be more than one word
    # classes = ['coughing','sneezing','drinking sipping', 'breathing', 'brushing teeth']
    classes = config["clap"]["descriptors"]
    # Add prompt
    # prompt = 'this is a sound of '
    prompt = config["clap"]["preamble"]
    class_prompts = [prompt + x for x in classes]
    # Load audio files
    # audio_files = ['/Users/mafaldadinis/Github/CAMM_app/audio_clips/test_audio.wav']

    # Load and initialize CLAP
    # Setting use_cuda = True will load the model on a GPU using CUDA
    clap_model = CLAP(version="2023", use_cuda=False)

    # compute text embeddings from natural text
    text_embeddings = clap_model.get_text_embeddings(class_prompts)

    # compute the audio embeddings from an audio file
    audio_embeddings = clap_model.get_audio_embeddings(audio_files, resample=True)

    # compute the similarity between audio_embeddings and text_embeddings
    similarity = clap_model.compute_similarity(audio_embeddings, text_embeddings)

    similarity = F.softmax(similarity, dim=1)
    values, indices = similarity[0].topk(config["clap"]["top_n_classes"])

    # Print the results
    print("Top predictions:")
    for value, index in zip(values, indices):
        print(f"{classes[index]:>16s}: {100 * value.item():.2f}%")

    # Create a list of tuples (class, similarity score)
    predictions = [
        (classes[index], value.item() * 100) for value, index in zip(values, indices)
    ]

    # Return the predictions sorted in descending order of similarity
    return predictions


if __name__ == "__main__":

    config = load_config()
    # Flask application setup
    app = Flask(__name__)
    app.config["SECRET_KEY"] = config["server"]["secret_key"]
    socketio = SocketIO(app)

    # Directories and file paths from configuration
    VIDEO_DIRECTORY = config["paths"]["video_directory"]
    AUDIO_CLIP_DIRECTORY = config["paths"]["audio_clip_directory"]
    PROCESSED_VIDEOS_FILE = config["paths"]["processed_videos_file"]
    MAX_CLIPS = config["audio"]["max_clips"]

    # Ensure directories exist
    os.makedirs(VIDEO_DIRECTORY, exist_ok=True)
    os.makedirs(AUDIO_CLIP_DIRECTORY, exist_ok=True)

    process_videos()  # Ensure videos are processed into HLS format

    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(
            os.path.join(app.root_path, 'static'),
            'favicon.ico', 
            mimetype='image/vnd.microsoft.icon'
        )


    @app.route('/get_videos')
    def get_videos():
        try:
            with open('videos/processed_videos.txt', 'r') as file:
                videos = file.read().splitlines()
            return jsonify(videos)
        except Exception as e:
            return jsonify([])

    @socketio.on("volume")
    def handle_volume(data):
        """Handle volume data from client."""
        print(f"Microphone Volume: {data['volume']}")

    @app.route("/")
    def index():
        """Serve the main HTML page with default values."""
        default_duration = config["audio"]["default_duration"]
        default_interval = config["audio"]["default_interval"]

        return render_template(
            config["server"]["main_page"],
            default_duration=default_duration,
            default_interval=default_interval,
        )

    @app.route("/videos/<path:filename>")
    def serve_video(filename):
        """Serve video files from the directory."""
        return send_from_directory(VIDEO_DIRECTORY, filename)

    @app.route("/audio-clips", methods=["GET"])
    def list_audio_clips():
        """List all stored audio clips."""
        clips = [
            {
                "filename": f,
                "timestamp": os.path.getmtime(os.path.join(AUDIO_CLIP_DIRECTORY, f)),
            }
            for f in os.listdir(AUDIO_CLIP_DIRECTORY)
            if f.endswith(".wav")
        ]
        return jsonify(sorted(clips, key=lambda x: x["timestamp"], reverse=True))

    @app.route("/audio-clips/<path:filename>", methods=["GET"])
    def download_audio_clip(filename):
        """Download a specific audio clip."""
        return send_from_directory(AUDIO_CLIP_DIRECTORY, filename)

    @socketio.on("audio-clip")
    def handle_audio_clip(data):
        """Process incoming audio clips."""
        audio_bytes = data.get("audio")
        if not audio_bytes:
            print("No audio data received.")
            emit("error", {"message": "No audio data received"})
            return

        print(f"Received audio data of size: {len(audio_bytes)} bytes")

        try:
            # Save the audio to a temporary file in WebM format
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            temp_file_path = os.path.join(
                AUDIO_CLIP_DIRECTORY, f"clip_{timestamp}.webm"
            )
            with open(temp_file_path, "wb") as temp_file:
                temp_file.write(audio_bytes)

            print(f"Saved raw WebM audio clip to: {temp_file_path}")

            # Convert WebM to WAV using FFmpeg
            wav_filename = f"clip_{timestamp}.wav"
            wav_file_path = os.path.join(AUDIO_CLIP_DIRECTORY, wav_filename)
            command = [
                "ffmpeg",
                "-i",
                temp_file_path,
                "-ar",
                str(config["ffmpeg"]["sample_rate"]),
                "-ac",
                str(config["ffmpeg"]["channels"]),
                "-filter:a",
                "volume=2dB",  # Adjust the volume level as needed "volume="
                wav_file_path,
            ]
            subprocess.run(command, check=True)
            print(f"Converted audio clip to WAV: {wav_file_path}")

            # Remove the temporary WebM file
            os.remove(temp_file_path)

            # Manage audio clip count
            manage_audio_clips()

            # Run inference with tinyCLAP
            # results = run_clap_inference(wav_file_path)

            # Run inference with MACLAP
            prediction = evaluate_msclap([wav_file_path])
            print(f"Prediction: {prediction}")
            # Emit prediction to client
            socketio.emit(
                "prediction",
                {
                    "class": prediction[0][0],  # Most likely class
                    "probability": prediction[0][
                        1
                    ],  # Probability of the most likely class
                },
            )
            emit(
                "inference-result", {"prediction": prediction, "filename": wav_filename}
            )
        except Exception as e:
            print(f"Error processing audio data: {e}")
            emit("error", {"message": "Error processing audio data"})

    # Start the Flask application
    socketio.run(
        app,
        host=config["server"]["host"],
        port=config["server"]["port"],
        debug=config["server"]["debug"],
    )
