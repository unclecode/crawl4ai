from functools import lru_cache
from pathlib import Path
import subprocess, os
import shutil
import tarfile
from .model_loader import *
import argparse
import urllib.request
from crawl4ai.config import MODEL_REPO_BRANCH
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

@lru_cache()
def get_available_memory(device):
    import torch
    if device.type == 'cuda':
        return torch.cuda.get_device_properties(device).total_memory
    elif device.type == 'mps':      
        return 48 * 1024 ** 3  # Assuming 8GB for MPS, as a conservative estimate
    else:
        return 0

@lru_cache()
def calculate_batch_size(device):
    available_memory = get_available_memory(device)
    
    if device.type == 'cpu':
        return 16
    elif device.type in ['cuda', 'mps']:
        # Adjust these thresholds based on your model size and available memory
        if available_memory >= 31 * 1024 ** 3:  # > 32GB
            return 256
        elif available_memory >= 15 * 1024 ** 3:  # > 16GB to 32GB
            return 128
        elif available_memory >= 8 * 1024 ** 3:  # 8GB to 16GB
            return 64
        else:
            return 32
    else:
        return 16  # Default batch size   
    
@lru_cache()
def get_device():
    import torch
    if torch.cuda.is_available():
        device = torch.device('cuda')
    elif torch.backends.mps.is_available():
        device = torch.device('mps')
    else:
        device = torch.device('cpu')
    return device   
    
def set_model_device(model):
    device = get_device()
    model.to(device)    
    return model, device

@lru_cache()
def get_home_folder():
    home_folder = os.path.join(Path.home(), ".crawl4ai")
    os.makedirs(home_folder, exist_ok=True)
    os.makedirs(f"{home_folder}/cache", exist_ok=True)
    os.makedirs(f"{home_folder}/models", exist_ok=True)
    return home_folder 

@lru_cache()
def load_bert_base_uncased():
    from transformers import BertTokenizer, BertModel, AutoTokenizer, AutoModel
    tokenizer = BertTokenizer.from_pretrained('bert-base-uncased', resume_download=None)
    model = BertModel.from_pretrained('bert-base-uncased', resume_download=None)
    model.eval()
    model, device = set_model_device(model)
    return tokenizer, model

@lru_cache()
def load_HF_embedding_model(model_name="BAAI/bge-small-en-v1.5") -> tuple:
    """Load the Hugging Face model for embedding.
    
    Args:
        model_name (str, optional): The model name to load. Defaults to "BAAI/bge-small-en-v1.5".
        
    Returns:
        tuple: The tokenizer and model.
    """
    from transformers import BertTokenizer, BertModel, AutoTokenizer, AutoModel
    tokenizer = AutoTokenizer.from_pretrained(model_name, resume_download=None)
    model = AutoModel.from_pretrained(model_name, resume_download=None)
    model.eval()
    model, device = set_model_device(model)
    return tokenizer, model

@lru_cache()
def load_text_classifier():
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    from transformers import pipeline
    import torch

    tokenizer = AutoTokenizer.from_pretrained("dstefa/roberta-base_topic_classification_nyt_news")
    model = AutoModelForSequenceClassification.from_pretrained("dstefa/roberta-base_topic_classification_nyt_news")
    model.eval()
    model, device = set_model_device(model)
    pipe = pipeline("text-classification", model=model, tokenizer=tokenizer)
    return pipe

@lru_cache()
def load_text_multilabel_classifier():
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    import numpy as np
    from scipy.special import expit
    import torch

    # # Check for available device: CUDA, MPS (for Apple Silicon), or CPU
    # if torch.cuda.is_available():
    #     device = torch.device("cuda")
    # elif torch.backends.mps.is_available():
    #     device = torch.device("mps")
    # else:
    #     device = torch.device("cpu")
    #     # return load_spacy_model(), torch.device("cpu")
    

    MODEL = "cardiffnlp/tweet-topic-21-multi"
    tokenizer = AutoTokenizer.from_pretrained(MODEL, resume_download=None)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL, resume_download=None)
    model.eval()
    model, device = set_model_device(model)
    class_mapping = model.config.id2label

    def _classifier(texts, threshold=0.5, max_length=64):
        tokens = tokenizer(texts, return_tensors='pt', padding=True, truncation=True, max_length=max_length)
        tokens = {key: val.to(device) for key, val in tokens.items()}  # Move tokens to the selected device

        with torch.no_grad():
            output = model(**tokens)

        scores = output.logits.detach().cpu().numpy()
        scores = expit(scores)
        predictions = (scores >= threshold) * 1

        batch_labels = []
        for prediction in predictions:
            labels = [class_mapping[i] for i, value in enumerate(prediction) if value == 1]
            batch_labels.append(labels)

        return batch_labels

    return _classifier, device

@lru_cache()
def load_nltk_punkt():
    import nltk
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt')
    return nltk.data.find('tokenizers/punkt')

@lru_cache()
def load_spacy_model():
    import spacy
    name = "models/reuters"
    home_folder = get_home_folder()
    model_folder = Path(home_folder) / name
    
    # Check if the model directory already exists
    if not (model_folder.exists() and any(model_folder.iterdir())):
        repo_url = "https://github.com/unclecode/crawl4ai.git"
        branch = MODEL_REPO_BRANCH 
        repo_folder = Path(home_folder) / "crawl4ai"
        
        print("[LOG] ⏬ Downloading Spacy model for the first time...")

        # Remove existing repo folder if it exists
        if repo_folder.exists():
            try:
                shutil.rmtree(repo_folder)
                if model_folder.exists():
                    shutil.rmtree(model_folder)
            except PermissionError:
                print("[WARNING] Unable to remove existing folders. Please manually delete the following folders and try again:")
                print(f"- {repo_folder}")
                print(f"- {model_folder}")
                return None

        try:
            # Clone the repository
            subprocess.run(
                ["git", "clone", "-b", branch, repo_url, str(repo_folder)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True
            )

            # Create the models directory if it doesn't exist
            models_folder = Path(home_folder) / "models"
            models_folder.mkdir(parents=True, exist_ok=True)

            # Copy the reuters model folder to the models directory
            source_folder = repo_folder / "models" / "reuters"
            shutil.copytree(source_folder, model_folder)

            # Remove the cloned repository
            shutil.rmtree(repo_folder)

            print("[LOG] ✅ Spacy Model downloaded successfully")
        except subprocess.CalledProcessError as e:
            print(f"An error occurred while cloning the repository: {e}")
            return None
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    try:
        return spacy.load(str(model_folder))
    except Exception as e:
        print(f"Error loading spacy model: {e}")
        return None

def download_all_models(remove_existing=False):
    """Download all models required for Crawl4AI."""
    if remove_existing:
        print("[LOG] Removing existing models...")
        home_folder = get_home_folder()
        model_folders = [
            os.path.join(home_folder, "models/reuters"),
            os.path.join(home_folder, "models"),
        ]
        for folder in model_folders:
            if Path(folder).exists():
                shutil.rmtree(folder)
        print("[LOG] Existing models removed.")

    # Load each model to trigger download
    # print("[LOG] Downloading BERT Base Uncased...")
    # load_bert_base_uncased()
    # print("[LOG] Downloading BGE Small EN v1.5...")
    # load_bge_small_en_v1_5()
    # print("[LOG] Downloading ONNX model...")
    # load_onnx_all_MiniLM_l6_v2()
    print("[LOG] Downloading text classifier...")
    _, device = load_text_multilabel_classifier()
    print(f"[LOG] Text classifier loaded on {device}")
    print("[LOG] Downloading custom NLTK Punkt model...")
    load_nltk_punkt()
    print("[LOG] ✅ All models downloaded successfully.")

def main():
    print("[LOG] Welcome to the Crawl4AI Model Downloader!")
    print("[LOG] This script will download all the models required for Crawl4AI.")
    parser = argparse.ArgumentParser(description="Crawl4AI Model Downloader")
    parser.add_argument('--remove-existing', action='store_true', help="Remove existing models before downloading")
    args = parser.parse_args()
    
    download_all_models(remove_existing=args.remove_existing)

if __name__ == "__main__":
    main()
