from typing import Any, AsyncGenerator

import pytest
from _pytest.mark.structures import ParameterSet

from crawl4ai.models import CrawlResultContainer, CrawlResult

RESULT: CrawlResult = CrawlResult(
    url="https://example.com", success=True, html="<html><body>Test content</body></html>"
)


def result_container_params() -> list[ParameterSet]:
    """Return a list of test parameters for the CrawlResultContainer tests.

    :return: List of test parameters for CrawlResultContainer tests containing tuple[result:CrawlResultContainer, expected:list[CrawlResult]]
    :rtype: list[ParameterSet]
    """

    async def async_generator(results: list[CrawlResult]) -> AsyncGenerator[CrawlResult, Any]:
        for result in results:
            yield result

    return [
        pytest.param(CrawlResultContainer(RESULT), [RESULT], id="result"),
        pytest.param(CrawlResultContainer([]), [], id="list_empty"),
        pytest.param(CrawlResultContainer([RESULT]), [RESULT], id="list_single"),
        pytest.param(CrawlResultContainer([RESULT, RESULT]), [RESULT, RESULT], id="list_multi"),
        pytest.param(CrawlResultContainer(async_generator([])), [], id="async_empty"),
        pytest.param(CrawlResultContainer(async_generator([RESULT])), [RESULT], id="async_single"),
        pytest.param(CrawlResultContainer(async_generator([RESULT, RESULT])), [RESULT, RESULT], id="async_multi"),
    ]


@pytest.mark.parametrize("result,expected", result_container_params())
def test_iter(result: CrawlResultContainer, expected: list[CrawlResult]):
    """Test __iter__ of the CrawlResultContainer."""
    if isinstance(result.source, AsyncGenerator):
        with pytest.raises(TypeError):
            for item in result:
                pass
        return

    results: list[CrawlResult] = []
    for item in result:
        results.append(item)

    assert results == expected


@pytest.mark.asyncio
@pytest.mark.parametrize("result,expected", result_container_params())
async def test_aiter(result: CrawlResultContainer, expected: list[CrawlResult]):
    """Test __aiter__ of the CrawlResultContainer."""
    results: list[CrawlResult] = []
    async for item in result:
        results.append(item)

    assert results == expected


@pytest.mark.parametrize("result,expected", result_container_params())
def test_getitem(result: CrawlResultContainer, expected: list[CrawlResult]):
    """Test the __getitem__ method of the CrawlResultContainer."""
    if isinstance(result.source, AsyncGenerator):
        with pytest.raises(TypeError):
            assert result[0] == expected[0]

        return

    for i in range(len(expected)):
        assert result[i] == expected[i]


@pytest.mark.parametrize("result,expected", result_container_params())
def test_len(result: CrawlResultContainer, expected: list[CrawlResult]):
    """Test the __len__ of the CrawlResultContainer."""
    if isinstance(result.source, AsyncGenerator):
        with pytest.raises(TypeError):
            assert len(result) == len(expected)

        return

    assert len(result) == len(expected)


def result_attributes() -> list[str]:
    """Return a list of attributes to test for CrawlResult

    :return: List of valid attributes, excluding private, callable, and deprecated attributes.
    :rtype: list[str]
    """

    # We check hasattr to avoid class only attribute error and failing on deprecated attributes.
    return [
        attr
        for attr in dir(RESULT)
        if attr in RESULT.model_fields or (hasattr(RESULT, attr) and isinstance(getattr(RESULT, attr), property))
    ]


@pytest.mark.parametrize("result,expected", result_container_params())
def test_getattribute(result: CrawlResultContainer, expected: list[CrawlResult]):
    """Test the __getattribute__ method of the CrawlResultContainer."""
    assert result.source is not None

    if isinstance(result.source, AsyncGenerator):
        for attr in result_attributes():
            with pytest.raises(TypeError):
                assert getattr(result, attr) == getattr(RESULT, attr)

        return

    if not expected:
        for attr in result_attributes():
            with pytest.raises(AttributeError):
                assert getattr(result, attr) == getattr(RESULT, attr)

        return

    for attr in result_attributes():
        assert getattr(result, attr) == getattr(RESULT, attr)


@pytest.mark.parametrize("result,expected", result_container_params())
def test_repr(result: CrawlResultContainer, expected: list[CrawlResult]):
    """Test the __repr__ method of the CrawlResultContainer."""
    if isinstance(result.source, AsyncGenerator):
        assert repr(result) == "CrawlResultContainer([])"

        return

    assert repr(result) == f"CrawlResultContainer({repr(expected)})"
