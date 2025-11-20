import os

from crawl4ai.utils import get_home_folder


def test_get_home_folder(monkeypatch, tmp_path):
    base_dir = tmp_path / "custom_base"
    monkeypatch.setenv("CRAWL4_AI_BASE_DIRECTORY", str(base_dir))

    home_folder = get_home_folder()
    assert home_folder == f"{base_dir}/.crawl4ai"
    assert os.path.exists(home_folder)
    assert os.path.exists(f"{home_folder}/cache")
    assert os.path.exists(f"{home_folder}/models")