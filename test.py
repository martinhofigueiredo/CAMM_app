from transformers import AutoModel, AutoTokenizer
import torch
import numpy as np
import librosa

def run_clap_inference(audio_path, model, tokenizer, config):
    """Run zero-shot inference on the audio file using a Hugging Face checkpoint."""
    try:
        # Load and preprocess the audio file
        audio_signal, sr = librosa.load(audio_path, sr=config["audio"]["sample_rate"])
        audio_signal = torch.tensor(audio_signal).float().unsqueeze(0)  # Add batch dim

        # Generate audio embeddings
        with torch.no_grad():
            audio_embed = model.get_audio_features(audio_signal)

        # Generate captions using the preamble and descriptors
        preamble = config["clap"]["preamble"]
        descriptors = config["clap"]["descriptors"]
        captions = [f"{preamble} {descriptor}" for descriptor in descriptors]

        # Prepare text features
        text_inputs = tokenizer(captions, return_tensors="pt", padding=True, truncation=True)
        with torch.no_grad():
            text_embed = model.get_text_features(**text_inputs)

        # Compute similarity scores
        similarity = torch.nn.functional.cosine_similarity(audio_embed, text_embed)

        return {
            "similarity_scores": similarity.cpu().tolist(),
            "captions": captions,
        }
    except Exception as e:
        print(f"Error during inference: {e}")
        return {"similarity_scores": [0], "error": str(e)}

# Load Hugging Face model and tokenizer
ckpt_path = "/Users/mafaldadinis/Github/CAMM_app/tinyCLAP/models/"  # Replace with the Hugging Face checkpoint path
model = AutoModel.from_pretrained(ckpt_path)
tokenizer = AutoTokenizer.from_pretrained(ckpt_path)

# Configuration dictionary
config = {
    "clap": {
        "preamble": "This is the sound of",
        "descriptors": [
            "applause",
            "a quiet room",
            "traffic noise",
            "a dog barking",
            "water running",
        ],
    },
    "audio": {
        "sample_rate": 16000,  # Match your model's input requirements
    },
}

# Path to the audio file
audio_path = "path/to/audio.wav"  # Provide the path to your audio file

# Run inference
results = run_clap_inference(audio_path, model, tokenizer, config)

print("Similarity Scores:", results["similarity_scores"])
print("Captions:", results["captions"])