from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from time import time

import pytest

from crawl4ai.async_dispatcher import RateLimiter


@pytest.mark.parametrize(
    "current_delay, headers, expected_delay",
    [
        pytest.param(1.0, {"retry-after": "5"}, 5.0, id="valid-retry-after"),
        pytest.param(1.0, {"retry-after": "invalid"}, None, id="invalid-retry-after"),
        pytest.param(1.0, None, None, id="no-headers"),
        pytest.param(
            1.0,
            {"ratelimit-remaining": "0", "ratelimit-reset": str(time() + 10)},
            10.0,
            id="valid-ratelimit-reset",
        ),
        pytest.param(
            1.0,
            {"x-ratelimit-remaining": "0", "x-ratelimit-reset": str(time() + 15)},
            15.0,
            id="valid-x-ratelimit-reset",
        ),
        pytest.param(
            1.0,
            {"x-rate-limit-remaining": "0", "x-rate-limit-reset": str(time() + 20)},
            20.0,
            id="valid-x-rate-limit-reset",
        ),
        pytest.param(
            1.0,
            {"x-ratelimit-userremaining": "0", "x-ratelimit-userreset": str(time() + 25)},
            25.0,
            id="valid-x-ratelimit-userreset",
        ),
        pytest.param(
            1.0,
            {"x-ratelimit-userpathremaining": "0", "x-ratelimit-userpathreset": str(time() + 30)},
            30.0,
            id="valid-x-ratelimit-userpathreset",
        ),
        pytest.param(
            1.0,
            {"ratelimit-reset": format_datetime(datetime.now(timezone.utc) + timedelta(seconds=40))},
            pytest.approx(40.0, abs=1.0),
            id="http-date-ratelimit-reset",
        ),
        pytest.param(
            1.0,
            {
                "x-ratelimit-remaining": "0",
                "x-ratelimit-reset": format_datetime(datetime.now(timezone.utc) + timedelta(seconds=50)),
            },
            pytest.approx(50.0, abs=1.0),
            id="http-date-x-ratelimit-reset",
        ),
        pytest.param(
            1.0,
            {"ratelimit-reset": str(time() + 60)},
            60.0,
            id="ratelimit-reset-only",
        ),
        pytest.param(
            1.0,
            {
                "x-ratelimit-userremaining": "10",
                "x-ratelimit-userreset": str(time() + 45),
                "x-ratelimit-userpathremaining": "0",
                "x-ratelimit-userpathreset": str(time() + 35),
            },
            35.0,
            id="userremaining-quota-userpathremaining-no-quota-userreset-ignored",
        ),
        pytest.param(
            1.0,
            {
                "x-ratelimit-userremaining": "10",
                "x-ratelimit-userpathremaining": "0",
                "x-ratelimit-userpathreset": str(time() + 35),
            },
            35.0,
            id="userremaining-quota-userpathremaining-no-quota",
        ),
        pytest.param(
            1.0,
            {
                "ratelimit-remaining": "-1",
                "ratelimit-reset": str(time() + 10),
            },
            10.0,
            id="ratelimit-remaining-negative",
        ),
        pytest.param(
            1.0,
            {
                "x-ratelimit-remaining": "-1",
                "x-ratelimit-reset": str(time() + 15),
            },
            15.0,
            id="x-ratelimit-remaining-negative",
        ),
        pytest.param(
            1.0,
            {
                "x-rate-limit-remaining": "-1",
                "x-rate-limit-reset": str(time() + 20),
            },
            20.0,
            id="x-rate-limit-remaining-negative",
        ),
        pytest.param(
            1.0,
            {
                "ratelimit-reset": str((time() + 10) * 1000),
            },
            10.0,
            id="ratelimit-reset-milliseconds",
        ),
        pytest.param(
            1.0,
            {
                "x-ratelimit-remaining": "0",
                "x-ratelimit-reset": str((time() + 15) * 1000),
            },
            15.0,
            id="x-ratelimit-reset-milliseconds",
        ),
        pytest.param(
            1.0,
            {
                "x-rate-limit-remaining": "0",
                "x-rate-limit-reset": str((time() + 20) * 1000),
            },
            20.0,
            id="x-rate-limit-reset-milliseconds",
        ),
    ],
)
def test_retry_after(current_delay: float, headers: dict[str, str] | None, expected_delay: float | None) -> None:
    rate_limiter = RateLimiter()
    delay = rate_limiter.retry_after(current_delay, headers)

    if expected_delay is not None:
        assert delay == pytest.approx(expected_delay, rel=1e-2)
    else:
        assert delay > current_delay  # Exponential backoff for invalid or missing headers
