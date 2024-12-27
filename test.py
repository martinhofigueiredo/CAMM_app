import torch
import torchaudio
import torchaudio.transforms as T
from pathlib import Path
from hyperpyyaml import load_hyperpyyaml
from tinyCLAP.tinyclap import CLAPBrain





if __name__ == "__main__":
    # Inputs
    audio_path = "./audio_clips/clip_20241227_164735_214124.wav"  # Update to your test audio file path
    captions = [
        "This is the sound of applause",
        "This is the sound of a quiet room",
        "This is the sound of traffic noise",
        "This is the sound of a dog barking",
        "This is the sound of water running",
    ]  # Provide your custom captions
    model_dir = "./tinyCLAP/models"  # Relative path to the model checkpoint directory
    hparams_path = "./tinyCLAP/hparams/distill_clap.yaml"  # Relative path to the hyperparameters file

    # Run zero-shot evaluation
    scores, captions = zero_shot_single_eval(audio_path, captions, model_dir, hparams_path)

    # Print results
    for caption, score in zip(captions, scores[0]):
        print(f"{caption}: {score:.4f}")