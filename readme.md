# Context Aware Multimedia application

> This is the list of milestones and the deadlines for submitting the deliverables corresponding to each milestone  (actual links for uploading are below):
>
> - [X] ~~Low fidelity prototype [__Nov 15th__]~~
> - [X] ~~Formal functional specification using UML [__Nov 29th__]~~
> - [X] ~~High Fidelity Prototype [__Dec 20th__]~~
> - [ ] final submission (report, prototype, vídeo presenting the prototype) ~~[__Jan  31st__]~~

> [!WARNING]
> 5% penalty for each week in delay

## Installation

1. Install ffmpeg and add to path to unsure its available to the application

```bash
sudo apt install ffmpeg
```

2. Create Virtual Environment and activate it
   Use python 3.11.9 or 3.12.3 for the environment

```bash
python -m venv .venv
# or
uv venv --python 3.11
source .venv/bin/activate
```

3. Install necessary requirements

```bash
pip install -r requirements.txt
```

4. Run the `server.py`

```bash
python server.py
```

## Configuration

The configuration file `config.toml` shows all the available parameters

```toml
# Server configuration
[server]
host = "127.0.0.1"                # IP address to bind the server
port = 5000                       # Port for the server
debug = true                      # Debug mode (true/false)
secret_key = "your_secret_key"    # Secret key for Flask
main_page = "index.html"          # Main HTML page to serve

# Paths for directories and files
[paths]
video_directory = "./videos"              # Directory for video files
audio_clip_directory = "./audio_clips"    # Directory for audio clips
processed_videos_file = "./videos/processed_videos.txt"  # File to track processed videos

# Audio processing configuration
[audio]
max_clips = 10                            # Maximum number of audio clips to retain
default_duration = 5                      # Default recording duration in seconds
default_interval = 30                     # Default interval between recordings in seconds

# FFmpeg configuration
[ffmpeg]
video_codec = "libx264"                   # Video codec for FFmpeg
audio_codec = "aac"                       # Audio codec for FFmpeg
hls_time = 10                             # HLS segment duration in seconds
playlist_type = "vod"                     # HLS playlist type
sample_rate = 16000                       # Audio sample rate for WAV conversion
channels = 1                              # Number of audio channels for WAV conversion

# CLAP model configuration
[clap]
preamble = "This is a sound of"         # Preamble to prepend to each descriptor
descriptors = [
    "applause",                           # List of descriptors for the CLAP model
    "a quiet room",
    "traffic noise",
    "a dog barking",
    "water running",
    "snore",
    "water dripping",
    "children laugh",
    "birds chirping"
]
top_n_classes = 9
```
