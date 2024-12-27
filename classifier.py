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
