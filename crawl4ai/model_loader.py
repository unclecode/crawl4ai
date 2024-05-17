from functools import lru_cache
from pathlib import Path
import subprocess, os
import shutil
from crawl4ai.config import MODEL_REPO_BRANCH
import argparse

def get_home_folder():
    home_folder = os.path.join(Path.home(), ".crawl4ai")
    os.makedirs(home_folder, exist_ok=True)
    os.makedirs(f"{home_folder}/cache", exist_ok=True)
    os.makedirs(f"{home_folder}/models", exist_ok=True)
    return home_folder 

@lru_cache()
def load_bert_base_uncased():
    from transformers import BertTokenizer, BertModel, AutoTokenizer, AutoModel
    tokenizer = BertTokenizer.from_pretrained('bert-base-uncased') #, resume_download=None)
    model = BertModel.from_pretrained('bert-base-uncased') #, resume_download=None)
    return tokenizer, model

@lru_cache()
def load_bge_small_en_v1_5():
    from transformers import BertTokenizer, BertModel, AutoTokenizer, AutoModel
    tokenizer = AutoTokenizer.from_pretrained('BAAI/bge-small-en-v1.5') #, resume_download=None)
    model = AutoModel.from_pretrained('BAAI/bge-small-en-v1.5') #, resume_download=None)
    model.eval()
    return tokenizer, model

@lru_cache()
def load_text_classifier():
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    from transformers import pipeline

    tokenizer = AutoTokenizer.from_pretrained("dstefa/roberta-base_topic_classification_nyt_news")
    model = AutoModelForSequenceClassification.from_pretrained("dstefa/roberta-base_topic_classification_nyt_news")
    pipe = pipeline("text-classification", model=model, tokenizer=tokenizer)

    return pipe

@lru_cache()
def load_text_multilabel_classifier():
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    import numpy as np
    from scipy.special import expit
    import torch

    MODEL = "cardiffnlp/tweet-topic-21-multi"
    tokenizer = AutoTokenizer.from_pretrained(MODEL, resume_download=None)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL, resume_download=None)
    class_mapping = model.config.id2label

    # Check for available device: CUDA, MPS (for Apple Silicon), or CPU
    if torch.cuda.is_available():
        device = torch.device("cuda")
    elif torch.backends.mps.is_available():
        device = torch.device("mps")
    else:
        device = torch.device("cpu")

    model.to(device)

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

    return _classifier

@lru_cache()
def load_nltk_punkt():
    import nltk
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt')
    return nltk.data.find('tokenizers/punkt')

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
    print("[LOG] Downloading BERT Base Uncased...")
    load_bert_base_uncased()
    print("[LOG] Downloading BGE Small EN v1.5...")
    load_bge_small_en_v1_5()
    print("[LOG] Downloading text classifier...")
    load_text_multilabel_classifier
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