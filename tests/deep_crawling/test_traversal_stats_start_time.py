"""TraversalStats must stamp each instance with its own creation time."""

import time
from datetime import datetime

from crawl4ai.models import TraversalStats


def test_each_instance_gets_its_own_start_time():
    first = TraversalStats()
    time.sleep(0.01)
    second = TraversalStats()
    assert first.start_time != second.start_time


def test_start_time_is_creation_time_not_import_time():
    assert abs((datetime.now() - TraversalStats().start_time).total_seconds()) < 5


def test_explicit_start_time_is_kept():
    stamped = datetime(2024, 1, 2, 3, 4, 5)
    assert TraversalStats(start_time=stamped).start_time == stamped
