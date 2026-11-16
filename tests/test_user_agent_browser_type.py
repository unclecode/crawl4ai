from crawl4ai.user_agent_generator import UserAgentGenerator


def _generator_with_chrome_stack(monkeypatch):
    generator = UserAgentGenerator()
    monkeypatch.setattr(
        generator,
        "get_browser_stack",
        lambda num_browsers=1: ["Chrome/119.0.6045.199"],
    )
    return generator


def test_generate_honours_firefox_browser_type(monkeypatch):
    generator = _generator_with_chrome_stack(monkeypatch)

    user_agent = generator.generate(browser_type="firefox")

    assert "Firefox/" in user_agent
    assert "Chrome/" not in user_agent
    assert "Edg/" not in user_agent


def test_generate_honours_edge_browser_type(monkeypatch):
    generator = _generator_with_chrome_stack(monkeypatch)

    user_agent = generator.generate(browser_type="edge")

    assert "Edg/" in user_agent
    assert "AppleWebKit/" in user_agent
