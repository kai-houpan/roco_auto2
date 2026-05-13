from config.settings import DIAGRAM_DIR, GAME_WINDOW_W, GAME_WINDOW_H
from core.recognizer import match_template


def locate_window() -> tuple[int, int] | None:
    """Find the game window. Returns (top_left_x, top_left_y) or None."""
    result = match_template("window.png", DIAGRAM_DIR)
    if result is None:
        return None
    # match_template returns center; convert to top-left
    return result[0] - GAME_WINDOW_W // 2, result[1] - GAME_WINDOW_H // 2


def quick_check_window(expected_x: int, expected_y: int) -> bool:
    """Lightweight check: is the window still at the expected position?"""
    result = match_template("window.png", DIAGRAM_DIR)
    if result is None:
        return False
    cx, cy = result
    wx = cx - GAME_WINDOW_W // 2
    wy = cy - GAME_WINDOW_H // 2
    return abs(wx - expected_x) < 20 and abs(wy - expected_y) < 20
