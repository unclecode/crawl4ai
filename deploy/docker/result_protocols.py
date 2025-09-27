# deploy/docker/result_protocols.py

from __future__ import annotations

from typing import Protocol, runtime_checkable, Iterable, Any, AsyncGenerator


@runtime_checkable
class ResultContainer(Protocol):
    """Protocol for objects that contain multiple crawl results."""

    @property
    def results(self) -> Iterable[Any]:
        """Extract individual results from container."""
        ...


@runtime_checkable
class SingleResult(Protocol):
    """Protocol for individual crawl result objects."""

    def to_dict(self) -> dict:
        """Convert single result to dict representation."""
        ...


@runtime_checkable
class AsyncResultGenerator(Protocol):
    """Protocol for async generators yielding results."""

    def __aiter__(self) -> AsyncGenerator[Any, None]:
        """Async iterator interface."""
        ...

    def __anext__(self) -> Any:
        """Async next interface."""
        ...