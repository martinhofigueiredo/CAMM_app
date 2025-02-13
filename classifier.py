#test classiefier integration

import tomli

def evaluate_msclap(audio_files):
    """
    This is an example using CLAP for zero-shot inference.
    """
    from msclap import CLAP
    import torch.nn.functional as F

    # Define classes for zero-shot
    # Should be in lower case and can be more than one word
    #classes = ['coughing','sneezing','drinking sipping', 'breathing', 'brushing teeth']
    classes = config["clap"]["descriptors"]
    # Add prompt
    #prompt = 'this is a sound of '
    prompt = config["clap"]["preamble"]
    class_prompts = [prompt + x for x in classes]
    #Load audio files
    #audio_files = ['/Users/mafaldadinis/Github/CAMM_app/audio_clips/test_audio.wav']

    # Load and initialize CLAP
    # Setting use_cuda = True will load the model on a GPU using CUDA
    clap_model = CLAP(version = '2023', use_cuda=False)

    # compute text embeddings from natural text
    text_embeddings = clap_model.get_text_embeddings(class_prompts)

    # compute the audio embeddings from an audio file
    audio_embeddings = clap_model.get_audio_embeddings(audio_files, resample=True)

    # compute the similarity between audio_embeddings and text_embeddings
    similarity = clap_model.compute_similarity(audio_embeddings, text_embeddings)

    similarity = F.softmax(similarity, dim=1)
    values, indices = similarity[0].topk(config["clap"]["top_n_classes"])

    # Print the results
    print("Top predictions:\n")
    for value, index in zip(values, indices):
        print(f"{classes[index]:>16s}: {100 * value.item():.2f}%")

    # Create a list of tuples (class, similarity score)
    predictions = [(classes[index], value.item() * 100) for value, index in zip(values, indices)]
    
    # Return the predictions sorted in descending order of similarity
    return predictions

# Load configuration from config.toml
CONFIG_PATH = "config.toml"
try:
    with open(CONFIG_PATH, "rb") as f:
        config = tomli.load(f)
except Exception as e:
    print(f"Error loading configuration file {CONFIG_PATH}: {e}")
    exit(1)


import os

def list_wav_files(folder_path):
    """
    Lists the file paths of all .wav files in a folder.

    Args:
        folder_path (str): Path to the folder containing .wav files.

    Returns:
        list: A list of file paths for all .wav files.
    """
    wav_file_paths = []
    
    
    # Iterate over all files in the folder
    for file_name in os.listdir(folder_path):
        # Check if the file has a .wav extension
        if file_name.lower().endswith('.wav'):
            file_path = os.path.join(folder_path, file_name)
            full_path = os.path.abspath(file_path)
            wav_file_paths.append(full_path)
    
    return wav_file_paths

if __name__ == '__main__':
    # Specify the folder containing .wav files
    folder_path = config["paths"]["audio_clip_directory"]

    # Get the list of .wav file paths
    wav_files = list_wav_files(folder_path)

    # Print the list of file paths
    print("WAV file paths:")
    for file_path in wav_files:
        print(file_path)
        evaluate_msclap([file_path])

    # Optionally, print the total count
    print(f"Total WAV files found: {len(wav_files)}")
    #evaluate_msclap(wav_files)


""" 
# from tinyCLAP.tinyclap import CLAPBrain  # Adjusted import for submodule directory
Initialize the CLAP model (update hparams and other dependencies as needed)
try:
    hparams = config["clap"]
    clap_model = CLAPBrain(modules=hparams['modules'], opt_class=None, hparams=hparams)
except Exception as e:
    print(f"Error loading CLAP model: {e}")
    clap_model = None

def run_clap_inference(audio_path):
    #Run zero-shot inference on the audio file using CLAP.
    if clap_model is None:
        return {"similarity_scores": [0]}

    try:
        # Load the audio file into a tensor
        audio_signal = torch.tensor(np.load(audio_path))  # Replace with appropriate loader
        audio_embed = clap_model.preprocess(audio_signal.unsqueeze(0))

        # Generate captions using the preamble and descriptors
        preamble = config["clap"]["preamble"]
        descriptors = config["clap"]["descriptors"]
        captions = [f"{preamble} {descriptor}" for descriptor in descriptors]

        # Prepare text features and compute similarity
        text_features = clap_model.prepare_txt_features(captions)
        similarity = clap_model.compute_sim(audio_embed, text_features)
        return {"similarity_scores": similarity.tolist(), "captions": captions}
    except Exception as e:
        print(f"Error during inference: {e}")
        return {"similarity_scores": [0]} import torch
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
"""
