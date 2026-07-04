import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from crawl4ai import model_loader


class _FakePretrained:
    from_pretrained = Mock()


@pytest.fixture(autouse=True)
def reset_pretrained_mock():
    _FakePretrained.from_pretrained.reset_mock()


def _fake_model():
    model = Mock()
    model.config.id2label = {}
    return model


def test_bert_loader_uses_current_from_pretrained_api(monkeypatch):
    tokenizer = object()
    model = _fake_model()
    _FakePretrained.from_pretrained.side_effect = [tokenizer, model]
    monkeypatch.setitem(
        sys.modules,
        "transformers",
        SimpleNamespace(BertTokenizer=_FakePretrained, BertModel=_FakePretrained),
    )
    monkeypatch.setattr(model_loader, "set_model_device", lambda value: (value, "cpu"))

    loaded_tokenizer, loaded_model = model_loader.load_bert_base_uncased()

    assert (loaded_tokenizer, loaded_model) == (tokenizer, model)
    assert _FakePretrained.from_pretrained.call_args_list == [
        (("bert-base-uncased",), {}),
        (("bert-base-uncased",), {}),
    ]


def test_embedding_loader_uses_current_from_pretrained_api(monkeypatch):
    tokenizer = object()
    model = _fake_model()
    _FakePretrained.from_pretrained.side_effect = [tokenizer, model]
    monkeypatch.setitem(
        sys.modules,
        "transformers",
        SimpleNamespace(AutoTokenizer=_FakePretrained, AutoModel=_FakePretrained),
    )
    monkeypatch.setattr(model_loader, "set_model_device", lambda value: (value, "cpu"))

    loaded_tokenizer, loaded_model = model_loader.load_HF_embedding_model("example/model")

    assert (loaded_tokenizer, loaded_model) == (tokenizer, model)
    assert _FakePretrained.from_pretrained.call_args_list == [
        (("example/model",), {}),
        (("example/model",), {}),
    ]


def test_multilabel_loader_uses_current_from_pretrained_api(monkeypatch):
    tokenizer = object()
    model = _fake_model()
    _FakePretrained.from_pretrained.side_effect = [tokenizer, model]
    monkeypatch.setitem(
        sys.modules,
        "transformers",
        SimpleNamespace(
            AutoTokenizer=_FakePretrained,
            AutoModelForSequenceClassification=_FakePretrained,
        ),
    )
    monkeypatch.setitem(sys.modules, "torch", SimpleNamespace())
    monkeypatch.setattr(model_loader, "set_model_device", lambda value: (value, "cpu"))

    classifier, device = model_loader.load_text_multilabel_classifier()

    assert callable(classifier)
    assert device == "cpu"
    assert _FakePretrained.from_pretrained.call_args_list == [
        (("cardiffnlp/tweet-topic-21-multi",), {}),
        (("cardiffnlp/tweet-topic-21-multi",), {}),
    ]
