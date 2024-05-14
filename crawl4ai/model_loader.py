from functools import lru_cache
from transformers import BertTokenizer, BertModel, AutoTokenizer, AutoModel
import spacy

@lru_cache()
def load_bert_base_uncased():
    tokenizer = BertTokenizer.from_pretrained('bert-base-uncased', resume_download=None)
    model = BertModel.from_pretrained('bert-base-uncased', resume_download=None)
    return tokenizer, model

@lru_cache()
def load_bge_small_en_v1_5():
    tokenizer = AutoTokenizer.from_pretrained('BAAI/bge-small-en-v1.5', resume_download=None)
    model = AutoModel.from_pretrained('BAAI/bge-small-en-v1.5', resume_download=None)
    model.eval()
    return tokenizer, model

@lru_cache()
def load_spacy_model():
    return spacy.load("models/reuters")
