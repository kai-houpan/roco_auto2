import os

# ---- Project root ----
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS_DIR = os.path.join(ROOT, "logs")

# ---- Active screen config (set by activate_config) ----
ACTIVE_CONFIG = "2560x1440_125"

# ---- Per-config parameters ----
# Values marked TODO are placeholders — fill in once assets are captured.
SCREEN_CONFIGS = {
    "2560x1440_125": {
        "screen_w": 2560,
        "screen_h": 1440,
        "game_window_w": 1442,
        "game_window_h": 938,
        "scroll_rel_x": 1160,
        "scroll_rel_y": 500,
        "state11_offset_x": 700,
        "state11_offset_y": 800,
        "close_offset_x": 1412,
        "close_offset_y": 17,
    },
    "1920x1080_100": {
        "screen_w": 1920,
        "screen_h": 1080,
        "game_window_w": 1150,
        "game_window_h": 750,
        "scroll_rel_x": 920,
        "scroll_rel_y": 400,
        "state11_offset_x": 500,
        "state11_offset_y": 400,
        "close_offset_x": 1120,
        "close_offset_y": 20,
    },
}

# ---- Resolved constants (updated by activate_config) ----
SCREEN_W = SCREEN_CONFIGS[ACTIVE_CONFIG]["screen_w"]
SCREEN_H = SCREEN_CONFIGS[ACTIVE_CONFIG]["screen_h"]
GAME_WINDOW_W = SCREEN_CONFIGS[ACTIVE_CONFIG]["game_window_w"]
GAME_WINDOW_H = SCREEN_CONFIGS[ACTIVE_CONFIG]["game_window_h"]
SCROLL_REL_X = SCREEN_CONFIGS[ACTIVE_CONFIG]["scroll_rel_x"]
SCROLL_REL_Y = SCREEN_CONFIGS[ACTIVE_CONFIG]["scroll_rel_y"]
STATE11_OFFSET_X = SCREEN_CONFIGS[ACTIVE_CONFIG]["state11_offset_x"]
STATE11_OFFSET_Y = SCREEN_CONFIGS[ACTIVE_CONFIG]["state11_offset_y"]
CLOSE_OFFSET_X = SCREEN_CONFIGS[ACTIVE_CONFIG]["close_offset_x"]
CLOSE_OFFSET_Y = SCREEN_CONFIGS[ACTIVE_CONFIG]["close_offset_y"]

# ---- Asset paths (resolved from ACTIVE_CONFIG) ----
def _assets_dir():
    return os.path.join(ROOT, "assets", "reference", ACTIVE_CONFIG)

def _diagram_dir():
    return os.path.join(_assets_dir(), "reference_diagram")

def _window_list_dir():
    return os.path.join(_diagram_dir(), "window_list")

def _eggs_dir():
    return os.path.join(_assets_dir(), "reference_list", "eggs")

def _gulus_dir():
    return os.path.join(_assets_dir(), "reference_list", "gulus")

ASSETS_DIR = _assets_dir()
DIAGRAM_DIR = _diagram_dir()
WINDOW_LIST_DIR = _window_list_dir()
EGGS_DIR = _eggs_dir()
GULUS_DIR = _gulus_dir()
EGGS_DICT_FILE = os.path.join(EGGS_DIR, "eggs_dictionary.md")
GULUS_DICT_FILE = os.path.join(GULUS_DIR, "gulus_dictionary.md")

# ---- Template Matching ----
MATCH_THRESHOLD = 0.8
WINDOW_MATCH_THRESHOLD = 0.7
MATCH_THRESHOLD_EGG = 0.95

# ---- Timing (seconds) ----
CLICK_WAIT = 1.0
SCROLL_WAIT = 0.3
POLL_INTERVAL = 0.5
ANIMATION_POLL_INTERVAL = 0.5
ANIMATION_TIMEOUT = 8.0

# ---- Retry Limits ----
MAX_CLICK_RETRIES = 3
MAX_SCROLL_RETRIES = 10
MAX_SCROLL_RETRIES_EGG = 100
MAX_WINDOW_LOST_CHECKS = 5
MAX_ANIMATION_RETRIES = 3

# ---- Extra verify delays (seconds) ----
DELAY_PUTIN_VERIFY = 2.0
DELAY_SITE_VERIFY = 2.0

# ---- Interception Driver ----
WHEEL_DELTA = 120
MOVE_DELAY = 0.02

# ---- Scroll ----
SCROLL_CLICKS = 24


def activate_config(name: str) -> bool:
    """Switch active screen config. Returns True on success, False if invalid name."""
    global ACTIVE_CONFIG, ASSETS_DIR, DIAGRAM_DIR, WINDOW_LIST_DIR
    global EGGS_DIR, GULUS_DIR, EGGS_DICT_FILE, GULUS_DICT_FILE
    global SCREEN_W, SCREEN_H, GAME_WINDOW_W, GAME_WINDOW_H
    global SCROLL_REL_X, SCROLL_REL_Y, STATE11_OFFSET_X, STATE11_OFFSET_Y
    global CLOSE_OFFSET_X, CLOSE_OFFSET_Y

    if name not in SCREEN_CONFIGS:
        return False

    ACTIVE_CONFIG = name
    cfg = SCREEN_CONFIGS[name]
    SCREEN_W = cfg["screen_w"]
    SCREEN_H = cfg["screen_h"]
    GAME_WINDOW_W = cfg["game_window_w"]
    GAME_WINDOW_H = cfg["game_window_h"]
    SCROLL_REL_X = cfg["scroll_rel_x"]
    SCROLL_REL_Y = cfg["scroll_rel_y"]
    STATE11_OFFSET_X = cfg["state11_offset_x"]
    STATE11_OFFSET_Y = cfg["state11_offset_y"]
    CLOSE_OFFSET_X = cfg["close_offset_x"]
    CLOSE_OFFSET_Y = cfg["close_offset_y"]

    ASSETS_DIR = _assets_dir()
    DIAGRAM_DIR = _diagram_dir()
    WINDOW_LIST_DIR = _window_list_dir()
    EGGS_DIR = _eggs_dir()
    GULUS_DIR = _gulus_dir()
    EGGS_DICT_FILE = os.path.join(EGGS_DIR, "eggs_dictionary.md")
    GULUS_DICT_FILE = os.path.join(GULUS_DIR, "gulus_dictionary.md")
    return True
