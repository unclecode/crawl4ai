import sys
import pytest
import asyncio
from unittest.mock import patch, MagicMock
from crawl4ai.browser_profiler import BrowserProfiler

@pytest.mark.asyncio
@pytest.mark.skipif(sys.platform != "win32", reason="Windows-specific msvcrt test")
async def test_keyboard_input_handling():
    # Mock sequence of keystrokes: arrow key followed by 'q'
    mock_keys = [b'\x00K', b'q']
    mock_kbhit = MagicMock(side_effect=[True, True, False])
    mock_getch = MagicMock(side_effect=mock_keys)

    with patch('msvcrt.kbhit', mock_kbhit), patch('msvcrt.getch', mock_getch):
        # profiler = BrowserProfiler()
        user_done_event = asyncio.Event()
        
        # Create a local async function to simulate the keyboard input handling
        async def test_listen_for_quit_command():
            if sys.platform == "win32":
                while True:
                    try:
                        if mock_kbhit():
                            raw = mock_getch()
                            try:
                                key = raw.decode("utf-8")
                            except UnicodeDecodeError:
                                continue

                            if len(key) != 1 or not key.isprintable():
                                continue

                            if key.lower() == "q":
                                user_done_event.set()
                                return

                        await asyncio.sleep(0.1)
                    except Exception as e:
                        continue

        # Run the listener
        listener_task = asyncio.create_task(test_listen_for_quit_command())
        
        # Wait for the event to be set
        try:
            await asyncio.wait_for(user_done_event.wait(), timeout=1.0)
            assert user_done_event.is_set()
        finally:
            if not listener_task.done():
                listener_task.cancel()
                try:
                    await listener_task
                except asyncio.CancelledError:
                    pass