"""Sentence chunking prepares the resources required by supported NLTK versions."""

import nltk
import pytest
from nltk.tokenize import _get_punkt_tokenizer
from nltk.tokenize.punkt import PunktParameters, save_punkt_params

from crawl4ai.chunking_strategy import NlpSentenceChunking
from crawl4ai.model_loader import load_nltk_punkt


@pytest.fixture
def nltk_data(tmp_path, monkeypatch):
    monkeypatch.setattr(nltk.data, "path", [str(tmp_path)])
    load_nltk_punkt.cache_clear()
    _get_punkt_tokenizer.cache_clear()
    yield tmp_path
    load_nltk_punkt.cache_clear()
    _get_punkt_tokenizer.cache_clear()


def install_resource(data_dir, resource):
    resource_dir = data_dir / "tokenizers" / resource
    resource_dir.mkdir(parents=True, exist_ok=True)
    if resource == "punkt_tab":
        language_dir = resource_dir / "english"
        language_dir.mkdir()
        save_punkt_params(PunktParameters(), dir=str(language_dir))


@pytest.mark.parametrize("legacy_installed", [False, True])
def test_sentence_chunking_prepares_missing_resources(
    nltk_data, monkeypatch, legacy_installed
):
    if legacy_installed:
        install_resource(nltk_data, "punkt")

    downloads = []

    def download(resource):
        downloads.append(resource)
        install_resource(nltk_data, resource)
        return True

    monkeypatch.setattr(nltk, "download", download)

    chunks = NlpSentenceChunking().chunk(
        "First sentence. Second sentence. First sentence."
    )

    assert chunks == ["First sentence.", "Second sentence.", "First sentence."]
    assert "punkt_tab" in downloads
    assert str(load_nltk_punkt()) == str(nltk_data / "tokenizers" / "punkt")


def test_sentence_chunking_uses_existing_resources(nltk_data, monkeypatch):
    for resource in ("punkt", "punkt_tab"):
        install_resource(nltk_data, resource)

    def download(resource):
        pytest.fail(f"Unexpected download of installed resource: {resource}")

    monkeypatch.setattr(nltk, "download", download)

    assert NlpSentenceChunking().chunk("One sentence. Another sentence.") == [
        "One sentence.",
        "Another sentence.",
    ]
