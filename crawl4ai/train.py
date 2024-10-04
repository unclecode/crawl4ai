import spacy
from spacy.training import Example
import random
import nltk
from nltk.corpus import reuters
import torch

def save_spacy_model_as_torch(nlp, model_dir="models/reuters"):
    # Extract the TextCategorizer component
    textcat = nlp.get_pipe("textcat")

    # Convert the weights to a PyTorch state dictionary
    state_dict = {name: torch.tensor(param.data) for name, param in textcat.model.named_parameters()}

    # Save the state dictionary
    torch.save(state_dict, f"{model_dir}/model_weights.pth")

    # Extract and save the vocabulary
    vocab = extract_vocab(nlp)
    with open(f"{model_dir}/vocab.txt", "w") as vocab_file:
        for word, idx in vocab.items():
            vocab_file.write(f"{word}\t{idx}\n")
    
    print(f"Model weights and vocabulary saved to: {model_dir}")

def extract_vocab(nlp):
    vocab = {word: i for i, word in enumerate(nlp.vocab.strings) if word.isalpha()}
    return vocab

def train_and_save_reuters_model(model_dir="models/reuters"):
    nltk.download('reuters')
    nltk.download('punkt')
    if not reuters.fileids():
        print("Reuters corpus not found.")
        return

    nlp = spacy.blank("en")
    textcat = nlp.add_pipe("textcat", config={"exclusive_classes": False, "architecture": "simple_cnn"})

    for label in reuters.categories():
        textcat.add_label(label)

    train_examples = []
    for fileid in reuters.fileids():
        categories = reuters.categories(fileid)
        text = reuters.raw(fileid)
        cats = {label: label in categories for label in reuters.categories()}
        doc = nlp.make_doc(text)
        example = Example.from_dict(doc, {'cats': cats})
        train_examples.append(example)

    nlp.initialize(lambda: train_examples)

    random.seed(1)
    for i in range(5):
        random.shuffle(train_examples)
        losses = {}
        batches = spacy.util.minibatch(train_examples, size=8)
        for batch in batches:
            nlp.update(batch, drop=0.2, losses=losses)
        print(f"Losses at iteration {i}: {losses}")

    nlp.to_disk(model_dir)
    print(f"Model saved to: {model_dir}")

def train_model(model_dir, additional_epochs=0):
    try:
        nlp = spacy.load(model_dir)
        print("Model loaded from disk.")
    except IOError:
        print("No existing model found. Starting with a new model.")
        nlp = spacy.blank("en")
        textcat = nlp.add_pipe("textcat", config={"exclusive_classes": False})
        for label in reuters.categories():
            textcat.add_label(label)

    train_examples = []
    for fileid in reuters.fileids():
        categories = reuters.categories(fileid)
        text = reuters.raw(fileid)
        cats = {label: label in categories for label in reuters.categories()}
        doc = nlp.make_doc(text)
        example = Example.from_dict(doc, {'cats': cats})
        train_examples.append(example)

    if 'textcat' not in nlp.pipe_names:
        nlp.initialize(lambda: train_examples)
    else:
        print("Continuing training with existing model.")

    random.seed(1)
    num_epochs = 5 + additional_epochs
    for i in range(num_epochs):
        random.shuffle(train_examples)
        losses = {}
        batches = spacy.util.minibatch(train_examples, size=8)
        for batch in batches:
            nlp.update(batch, drop=0.2, losses=losses)
        print(f"Losses at iteration {i}: {losses}")

    nlp.to_disk(model_dir)
    print(f"Model saved to: {model_dir}")

def load_model_and_predict(model_dir, text, tok_k=3):
    nlp = spacy.load(model_dir)
    doc = nlp(text)
    top_categories = sorted(doc.cats.items(), key=lambda x: x[1], reverse=True)[:tok_k]
    print(f"Top {tok_k} categories:")
    for category, score in top_categories:
        print(f"{category}: {score:.4f}")
    return top_categories

if __name__ == "__main__":
    model_directory = "models/reuters"
    train_and_save_reuters_model()
    train_model(model_directory, additional_epochs=5)
    example_text = "Apple Inc. is reportedly buying a startup for $1 billion"
    load_model_and_predict(model_directory, example_text)
