def evaluate_msclap(audio_files):
    """
    This is an example using CLAP for zero-shot inference.
    """
    from msclap import CLAP
    import torch.nn.functional as F

    # Define classes for zero-shot
    # Should be in lower case and can be more than one word
    #classes = ['coughing','sneezing','drinking sipping', 'breathing', 'brushing teeth']
    # Add prompt
    #prompt = 'this is a sound of '
    class_prompts = [config["CLAP"]["preamble"] + x for x in config["CLAP"]["descriptors"]]
    #Load audio files
    audio_files = ['/Users/mafaldadinis/Github/CAMM_app/audio_clips/test_audio.wav']

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
    values, indices = similarity[0].topk(config["CLAP"]["top_n_classes"])

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


if __name__ == '__main__':
    audio_clips