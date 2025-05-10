import email.utils
import time
from dataclasses import dataclass
from typing import Callable, List, Optional
from urllib.parse import urlparse

import pytest
from _pytest.mark.structures import ParameterSet  # pyright: ignore[reportPrivateImportUsage]

from crawl4ai.async_dispatcher import RateLimiter, RateLimitStatus
from crawl4ai.models import CrawlResult, CrawlResultContainer, DomainState


@dataclass
class RateLimitRequest:
    status_code: int = 200
    headers: Callable[[], Optional[dict[str, str]]] = lambda: None


@dataclass
class RateLimitExpected:
    status: RateLimitStatus = RateLimitStatus.CONTINUE
    rate: float = 5
    capacity: int = 20
    retry_after: float = 0
    tokens: int = 19
    consecutive_failures: int = 0
    took: Optional[float] = 0


def reset_time(after: int) -> str:
    """Return a string representation of the time in the future.

    :param after: The number of seconds to add to the current time.
    :type after: int
    :return: A string representation of the time in the future.
    :rtype: str
    """
    return str(time.time() + after)


def ratelimit_params() -> List[ParameterSet]:
    return [
        pytest.param(
            RateLimiter(),
            [RateLimitRequest(status_code=429)],
            RateLimitExpected(
                status=RateLimitStatus.RETRY,
                retry_after=1.0,
                tokens=0,
                consecutive_failures=1,
            ),
            id="status-code-429",
        ),
        pytest.param(
            RateLimiter(),
            [RateLimitRequest(status_code=503)],
            RateLimitExpected(
                status=RateLimitStatus.RETRY,
                retry_after=1.0,
                tokens=0,
                consecutive_failures=1,
            ),
            id="status-code-503",
        ),
        pytest.param(
            RateLimiter(max_retries=3, max_delay=1, max_burst=1),
            [RateLimitRequest(status_code=503)] * 3,
            RateLimitExpected(
                status=RateLimitStatus.NO_RETRY,
                retry_after=1.0,
                tokens=0,
                consecutive_failures=3,
                capacity=1,
                took=None,  # Can't predict exponential backoff delay due to randomness.
            ),
            id="max-consecutive-failures",
        ),
        pytest.param(
            RateLimiter(),
            [RateLimitRequest(headers=lambda: {"retry-after": "1"})],
            RateLimitExpected(
                retry_after=1.0,
                tokens=0,
            ),
            id="retry-after",
        ),
        pytest.param(
            RateLimiter(),
            [RateLimitRequest(headers=lambda: {"retry-after": "1"}), RateLimitRequest()],
            RateLimitExpected(
                retry_after=1.0,
                tokens=4,
                took=1.0,
            ),
            id="retry-after-next-request",
        ),
        pytest.param(
            RateLimiter(),
            [
                RateLimitRequest(
                    headers=lambda: {
                        "x-ratelimit-remaining": "0",
                        "x-ratelimit-reset": reset_time(10),
                        "x-ratelimit-limit": "100",
                    }
                )
            ],
            RateLimitExpected(
                retry_after=15.0,
                rate=10,
                tokens=0,
                capacity=20,
            ),
            id="x-ratelimit",
        ),
        pytest.param(
            RateLimiter(),
            [
                RateLimitRequest(
                    headers=lambda: {
                        "ratelimit-remaining": "0",
                        "ratelimit-reset": reset_time(20),
                        "ratelimit-limit": "100",
                    }
                )
            ],
            RateLimitExpected(
                retry_after=10.0,
                tokens=0,
                capacity=20,
            ),
            id="ratelimit-headers",
        ),
        pytest.param(
            RateLimiter(),
            [
                RateLimitRequest(
                    headers=lambda: {
                        "x-rate-limit-remaining": "0",
                        "x-rate-limit-reset": reset_time(40),
                        "x-rate-limit-limit": "100",
                    }
                )
            ],
            RateLimitExpected(
                retry_after=20.0,
                rate=2.5,
                tokens=0,
                capacity=20,
            ),
            id="x-rate-limit-headers",
        ),
        pytest.param(
            RateLimiter(),
            [
                RateLimitRequest(
                    headers=lambda: {
                        "x-ratelimit-userremaining": "0",
                        "x-ratelimit-userreset": reset_time(20),
                        "x-ratelimit-userlimit": "100",
                    }
                )
            ],
            RateLimitExpected(
                retry_after=25.0,
                tokens=0,
                capacity=20,
            ),
            id="x-ratelimit-user-headers",
        ),
        pytest.param(
            RateLimiter(),
            [
                RateLimitRequest(
                    headers=lambda: {
                        "x-ratelimit-userpathremaining": "0",
                        "x-ratelimit-userpathreset": reset_time(20),
                        "x-ratelimit-userpathlimit": "100",
                    }
                )
            ],
            RateLimitExpected(
                retry_after=30.0,
                tokens=0,
                capacity=20,
            ),
            id="x-ratelimit-userpath-headers",
        ),
        pytest.param(
            RateLimiter(),
            [
                RateLimitRequest(
                    headers=lambda: {
                        "ratelimit-remaining": "0",
                        "ratelimit-reset": str((time.time() + 20) * 1e3),
                        "ratelimit-limit": "100",
                    }
                )
            ],
            RateLimitExpected(
                retry_after=10.0,
                tokens=0,
                capacity=20,
            ),
            id="reset-milliseconds",
        ),
        pytest.param(
            RateLimiter(),
            [
                RateLimitRequest(
                    headers=lambda: {
                        "ratelimit-remaining": "0",
                        "ratelimit-reset": str((time.time() + 20) * 1e6),
                        "ratelimit-limit": "100",
                    }
                )
            ],
            RateLimitExpected(
                retry_after=10.0,
                tokens=0,
                capacity=20,
            ),
            id="reset-microseconds",
        ),
        pytest.param(
            RateLimiter(),
            [
                RateLimitRequest(
                    headers=lambda: {
                        "ratelimit-remaining": "0",
                        "ratelimit-reset": str((time.time() + 20) * 1e9),
                        "ratelimit-limit": "100",
                    }
                )
            ],
            RateLimitExpected(
                retry_after=10.0,
                tokens=0,
                capacity=20,
            ),
            id="reset-nanoseconds",
        ),
        pytest.param(
            RateLimiter(),
            [
                RateLimitRequest(
                    headers=lambda: {
                        "ratelimit-remaining": "0",
                        "ratelimit-reset": email.utils.formatdate(time.time() + 20, usegmt=True),
                        "ratelimit-limit": "100",
                    }
                )
            ],
            RateLimitExpected(
                retry_after=20.0,
                tokens=0,
                capacity=20,
            ),
            id="reset-rfc2822",
        ),
        pytest.param(
            RateLimiter(),
            [
                RateLimitRequest(
                    headers=lambda: {
                        "ratelimit-remaining": "0",
                        "ratelimit-reset": reset_time(10),
                        "ratelimit-limit": "10",
                    }
                )
            ],
            RateLimitExpected(retry_after=20.0, rate=1.0, tokens=0, capacity=10),
            id="reduced-limit",
        ),
        pytest.param(
            RateLimiter(),
            [
                RateLimitRequest(
                    headers=lambda: {
                        "ratelimit-remaining": "1",
                        "ratelimit-reset": reset_time(10),
                        "ratelimit-limit": "10",
                    }
                )
            ],
            RateLimitExpected(rate=1.0, tokens=1, capacity=10),
            id="remaining-tokens",
        ),
        pytest.param(
            RateLimiter(),
            [RateLimitRequest()],
            RateLimitExpected(),
            id="no-headers",
        ),
        pytest.param(
            RateLimiter(),
            [RateLimitRequest()] * 2,
            RateLimitExpected(
                tokens=18,
            ),
            id="two-requests",
        ),
        pytest.param(
            RateLimiter(),
            [RateLimitRequest()] * 20,
            RateLimitExpected(
                tokens=0,
            ),
            id="capacity-requests",
        ),
        pytest.param(
            RateLimiter(),
            [RateLimitRequest()] * 21,
            RateLimitExpected(
                tokens=0,
                took=1 / 5,
            ),
            id="more-than-capacity-requests",
        ),
        pytest.param(
            RateLimiter(),
            [
                RateLimitRequest(
                    headers=lambda: {
                        "retry-after": "1",
                        "ratelimit-remaining": "1",
                        "ratelimit-reset": reset_time(10),
                        "ratelimit-limit": "10",
                    }
                )
            ],
            RateLimitExpected(retry_after=1.0, rate=1.0, tokens=0, capacity=10),
            id="retry-after-override",
        ),
        pytest.param(
            RateLimiter(),
            [
                RateLimitRequest(
                    headers=lambda: {
                        "x-ratelimit-userremaining": "0",
                        "x-ratelimit-userreset": reset_time(50),
                        "x-ratelimit-userlimit": "100",
                        "x-ratelimit-userpathremaining": "0",
                        "x-ratelimit-userpathreset": reset_time(20),
                        "x-ratelimit-userpathlimit": "100",
                    }
                )
            ],
            RateLimitExpected(
                retry_after=40.0,
                rate=2.0,
                tokens=0,
            ),
            id="worst-case-reset",
        ),
        pytest.param(
            RateLimiter(),
            [
                RateLimitRequest(
                    headers=lambda: {
                        "x-ratelimit-userremaining": "1",
                        "x-ratelimit-userreset": reset_time(50),
                        "x-ratelimit-userlimit": "100",
                        "x-ratelimit-userpathremaining": "0",
                        "x-ratelimit-userpathreset": reset_time(20),
                        "x-ratelimit-userpathlimit": "100",
                        "x-ratelimit-remaining": "0",
                        "x-ratelimit-reset": reset_time(20),
                        "x-ratelimit-limit": "10",
                    }
                )
            ],
            RateLimitExpected(
                retry_after=40.0,  # From x-ratelimit-userreset
                rate=0.2,  # From x-ratelimit-reset and x-ratelimit-limit
                tokens=0,  # From x-ratelimit-userpathremaining
                capacity=10,  # From x-ratelimit-limit
            ),
            id="worst-case-overall",
        ),
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize("limiter, requests, expected", ratelimit_params())
async def test_ratelimiter(limiter: RateLimiter, requests: List[RateLimitRequest], expected: RateLimitExpected) -> None:
    assert requests, "No requests provided for testing"

    url: str = "https://example.com"
    request: RateLimitRequest
    status: Optional[RateLimitStatus] = None
    start: float = time.monotonic()
    for request in requests:
        await limiter.wait_if_needed(url)
        # Header construction is delayed until the request is made to avoid
        # issues with absolute times.
        result: CrawlResult = CrawlResult(
            url=url, html="", success=True, response_headers=request.headers(), status_code=request.status_code
        )
        status = await limiter.update(CrawlResultContainer(result))

    end: float = time.monotonic()
    took: float = end - start
    assert status == expected.status
    if expected.took is not None:
        assert took == pytest.approx(expected.took, abs=1e-2)

    # Lookup internal state.
    domain: str = urlparse(url).netloc
    state: Optional[DomainState] = limiter._domains.get(domain)
    assert state

    assert state._rate == expected.rate
    assert state._capacity == expected.capacity
    if expected.retry_after > 0:
        assert state._backoff_until == pytest.approx(end + expected.retry_after, rel=1e-2)
    assert state._tokens == expected.tokens
    assert state._consecutive_failures == expected.consecutive_failures
