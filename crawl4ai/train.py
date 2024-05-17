import spacy
from spacy.training import Example
import random
import nltk
from nltk.corpus import reuters
import torch

def save_spacy_model_as_torch(nlp, model_dir="models/reuters"):
    # Extract the TextCategorizer component
    textcat = nlp.get_pipe("textcat_multilabel")

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
    # Extract vocabulary from the SpaCy model
    vocab = {word: i for i, word in enumerate(nlp.vocab.strings)}
    return vocab

nlp = spacy.load("models/reuters")
save_spacy_model_as_torch(nlp, model_dir="models")

def train_and_save_reuters_model(model_dir="models/reuters"):
    # Ensure the Reuters corpus is downloaded
    nltk.download('reuters')
    nltk.download('punkt')
    if not reuters.fileids():
        print("Reuters corpus not found.")
        return

    # Load a blank English spaCy model
    nlp = spacy.blank("en")

    # Create a TextCategorizer with the ensemble model for multi-label classification
    textcat = nlp.add_pipe("textcat_multilabel")

    # Add labels to text classifier
    for label in reuters.categories():
        textcat.add_label(label)

    # Prepare training data
    train_examples = []
    for fileid in reuters.fileids():
        categories = reuters.categories(fileid)
        text = reuters.raw(fileid)
        cats = {label: label in categories for label in reuters.categories()}
        # Prepare spacy Example objects
        doc = nlp.make_doc(text)
        example = Example.from_dict(doc, {'cats': cats})
        train_examples.append(example)

    # Initialize the text categorizer with the example objects
    nlp.initialize(lambda: train_examples)

    # Train the model
    random.seed(1)
    spacy.util.fix_random_seed(1)
    for i in range(5):  # Adjust iterations for better accuracy
        random.shuffle(train_examples)
        losses = {}
        # Create batches of data
        batches = spacy.util.minibatch(train_examples, size=8)
        for batch in batches:
            nlp.update(batch, drop=0.2, losses=losses)
        print(f"Losses at iteration {i}: {losses}")

    # Save the trained model
    nlp.to_disk(model_dir)
    print(f"Model saved to: {model_dir}")

def train_model(model_dir, additional_epochs=0):
    # Load the model if it exists, otherwise start with a blank model
    try:
        nlp = spacy.load(model_dir)
        print("Model loaded from disk.")
    except IOError:
        print("No existing model found. Starting with a new model.")
        nlp = spacy.blank("en")
        textcat = nlp.add_pipe("textcat_multilabel")
        for label in reuters.categories():
            textcat.add_label(label)

    # Prepare training data
    train_examples = []
    for fileid in reuters.fileids():
        categories = reuters.categories(fileid)
        text = reuters.raw(fileid)
        cats = {label: label in categories for label in reuters.categories()}
        doc = nlp.make_doc(text)
        example = Example.from_dict(doc, {'cats': cats})
        train_examples.append(example)

    # Initialize the model if it was newly created
    if 'textcat_multilabel' not in nlp.pipe_names:
        nlp.initialize(lambda: train_examples)
    else:
        print("Continuing training with existing model.")

    # Train the model
    random.seed(1)
    spacy.util.fix_random_seed(1)
    num_epochs = 5 + additional_epochs
    for i in range(num_epochs):
        random.shuffle(train_examples)
        losses = {}
        batches = spacy.util.minibatch(train_examples, size=8)
        for batch in batches:
            nlp.update(batch, drop=0.2, losses=losses)
        print(f"Losses at iteration {i}: {losses}")

    # Save the trained model
    nlp.to_disk(model_dir)
    print(f"Model saved to: {model_dir}")

def load_model_and_predict(model_dir, text, tok_k = 3):
    # Load the trained model from the specified directory
    nlp = spacy.load(model_dir)
    
    # Process the text with the loaded model
    doc = nlp(text)
    
    # gee top 3 categories
    top_categories = sorted(doc.cats.items(), key=lambda x: x[1], reverse=True)[:tok_k]
    print(f"Top {tok_k} categories:")
    
    return top_categories    

if __name__ == "__main__":
    train_and_save_reuters_model()
    train_model("models/reuters", additional_epochs=5)
    model_directory = "reuters_model_10"
    print(reuters.categories())
    example_text = "Apple Inc. is reportedly buying a startup for $1 billion"
    r =load_model_and_predict(model_directory, example_text)
    print(r)