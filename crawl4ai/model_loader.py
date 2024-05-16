from functools import lru_cache
from pathlib import Path
import subprocess, os
import shutil
from .config import MODEL_REPO_BRANCH
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
    tokenizer = BertTokenizer.from_pretrained('bert-base-uncased', resume_download=None)
    model = BertModel.from_pretrained('bert-base-uncased', resume_download=None)
    return tokenizer, model

@lru_cache()
def load_bge_small_en_v1_5():
    from transformers import BertTokenizer, BertModel, AutoTokenizer, AutoModel
    tokenizer = AutoTokenizer.from_pretrained('BAAI/bge-small-en-v1.5', resume_download=None)
    model = AutoModel.from_pretrained('BAAI/bge-small-en-v1.5', resume_download=None)
    model.eval()
    return tokenizer, model

@lru_cache()
def load_spacy_en_core_web_sm():
    import spacy
    try:
        print("[LOG] Loading spaCy model")
        nlp = spacy.load("en_core_web_sm")
    except IOError:
        print("[LOG] ⏬ Downloading spaCy model for the first time")
        spacy.cli.download("en_core_web_sm")
        nlp = spacy.load("en_core_web_sm")    
    print("[LOG] ✅ spaCy model loaded successfully")
    return nlp


@lru_cache()
def load_spacy_model():
    import spacy
    name = "models/reuters"
    home_folder = get_home_folder()
    model_folder = os.path.join(home_folder, name)
    
    # Check if the model directory already exists
    if not (Path(model_folder).exists() and any(Path(model_folder).iterdir())):
        repo_url = "https://github.com/unclecode/crawl4ai.git"
        # branch = "main"
        branch = MODEL_REPO_BRANCH 
        repo_folder = os.path.join(home_folder, "crawl4ai")
        model_folder = os.path.join(home_folder, name)

        print("[LOG] ⏬ Downloading model for the first time...")

        # Remove existing repo folder if it exists
        if Path(repo_folder).exists():
            shutil.rmtree(repo_folder)
            shutil.rmtree(model_folder)

        try:
            # Clone the repository
            subprocess.run(
                ["git", "clone", "-b", branch, repo_url, repo_folder],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True
            )

            # Create the models directory if it doesn't exist
            models_folder = os.path.join(home_folder, "models")
            os.makedirs(models_folder, exist_ok=True)

            # Copy the reuters model folder to the models directory
            source_folder = os.path.join(repo_folder, "models/reuters")
            shutil.copytree(source_folder, model_folder)

            # Remove the cloned repository
            shutil.rmtree(repo_folder)

            # Print completion message
            print("[LOG] ✅ Model downloaded successfully")
        except subprocess.CalledProcessError as e:
            print(f"An error occurred while cloning the repository: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")

    return spacy.load(model_folder)


def download_all_models(remove_existing=False):
    """Download all models required for Crawl4AI."""
    print("[LOG] Welcome to the Crawl4AI Model Downloader!")
    print("[LOG] This script will download all the models required for Crawl4AI.")
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
    print("[LOG] Downloading spaCy EN Core Web SM...")
    load_spacy_en_core_web_sm()
    print("[LOG] Downloading custom spaCy model...")
    load_spacy_model()
    print("[LOG] ✅ All models downloaded successfully.")

def main():
    parser = argparse.ArgumentParser(description="Crawl4AI Model Downloader")
    parser.add_argument('--remove-existing', action='store_true', help="Remove existing models before downloading")
    args = parser.parse_args()
    
    download_all_models(remove_existing=args.remove_existing)

if __name__ == "__main__":
    main()