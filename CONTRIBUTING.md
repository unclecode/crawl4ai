# Contributing to Crawl4AI

Thank you for your interest in contributing to Crawl4AI!

## Getting Started

1. Fork the repository
2. Clone your fork
3. Install in development mode: `pip install -e ".[all]"`
4. Run tests: `pytest tests/`

## Contributing New LLM Providers

### 1. Create Provider Class

Create `crawl4ai/providers/your_provider.py`:

```python
from litellm import CustomLLM
from litellm.types.utils import ModelResponse

class YourProvider(CustomLLM):
    async def acompletion(self, model, messages, **kwargs) -> ModelResponse:
        # Implement async completion
        pass

    def completion(self, model, messages, **kwargs) -> ModelResponse:
        # Implement sync completion
        pass
```

### 2. Register Provider

Update `crawl4ai/providers/__init__.py` to register your provider:

```python
from .your_provider import YourProvider

def register_your_provider():
    import litellm
    your_provider = YourProvider()
    litellm.custom_provider_map = [
        {"provider": "your-provider", "custom_handler": your_provider}
    ]
```

### 3. Add Optional Dependency

Update `pyproject.toml` with your SDK dependency:

```toml
[project.optional-dependencies]
your-provider = ["your-sdk>=1.0.0"]
```

### 4. Write Tests

Add tests at:
- `tests/unit/test_your_provider.py` - Unit tests for the provider
- `tests/integration/test_your_integration.py` - Integration tests

### 5. Add Documentation

- Update `docs/md_v2/extraction/llm-strategies.md` with a provider example
- Consider creating a dedicated doc page at `docs/md_v2/extraction/your-provider.md`

## Pull Request Process

1. Ensure all tests pass: `pytest tests/`
2. Update documentation as needed
3. Add a CHANGELOG.md entry under `[Unreleased]`
4. Submit PR against the `main` branch

## Code Style

- Follow PEP 8
- Use type hints where possible
- Add docstrings to public functions and classes
- Keep functions focused and testable

## Testing

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/unit/test_your_provider.py -v

# Run with coverage
pytest tests/ --cov=crawl4ai
```

## Questions?

Open an issue for discussion before starting major changes.
