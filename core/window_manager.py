import os

from config.settings import GAME_WINDOW_W, GAME_WINDOW_H, WINDOW_MATCH_THRESHOLD, WINDOW_LIST_DIR
from core.recognizer import match_template


def _templates() -> list[str]:
    """Return sorted list of PNG filenames in WINDOW_LIST_DIR."""
    if not os.path.isdir(WINDOW_LIST_DIR):
        return []
    return sorted(
        f for f in os.listdir(WINDOW_LIST_DIR) if f.lower().endswith(".png")
    )


def locate_window() -> tuple[int, int] | None:
    """Find the game window by trying every template in window_list/.
    Returns (top_left_x, top_left_y) or None.
    """
    for fname in _templates():
        result = match_template(fname, WINDOW_LIST_DIR,
                                threshold=WINDOW_MATCH_THRESHOLD)
        if result is not None:
            # match_template returns center; convert to top-left
            return result[0] - GAME_WINDOW_W // 2, result[1] - GAME_WINDOW_H // 2
    return None


def quick_check_window(expected_x: int, expected_y: int) -> bool:
    """Lightweight check: is the window still at the expected position?"""
    for fname in _templates():
        result = match_template(fname, WINDOW_LIST_DIR)
        if result is not None:
            cx, cy = result
            wx = cx - GAME_WINDOW_W // 2
            wy = cy - GAME_WINDOW_H // 2
            return abs(wx - expected_x) < 20 and abs(wy - expected_y) < 20
    return False
