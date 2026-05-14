import os

# ---- Paths ----
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(ROOT, "assets", "reference")
DIAGRAM_DIR = os.path.join(ASSETS_DIR, "reference_diagram")
WINDOW_LIST_DIR = os.path.join(DIAGRAM_DIR, "window_list")
EGGS_DIR = os.path.join(ASSETS_DIR, "reference_list", "eggs")
GULUS_DIR = os.path.join(ASSETS_DIR, "reference_list", "gulus")
LOGS_DIR = os.path.join(ROOT, "logs")

EGGS_DICT_FILE = os.path.join(EGGS_DIR, "eggs_dictionary.md")
GULUS_DICT_FILE = os.path.join(GULUS_DIR, "gulus_dictionary.md")

# ---- Screen / Window ----
SCREEN_W = 2560
SCREEN_H = 1440
GAME_WINDOW_W = 1442
GAME_WINDOW_H = 938

# ---- Template Matching ----
MATCH_THRESHOLD = 0.8
WINDOW_MATCH_THRESHOLD = 0.7
MATCH_THRESHOLD_EGG = 0.95

# ---- Timing (seconds) ----
CLICK_WAIT = 1.0
SCROLL_WAIT = 0.3
POLL_INTERVAL = 0.5
ANIMATION_POLL_INTERVAL = 0.5   # STATE_10 动画等待，不受通用规则影响
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
WHEEL_DELTA = 120          # Windows 标准：每个滚轮齿 = 120
MOVE_DELAY = 0.02          # Interception 移动后到点击前的微延迟

# ---- Scroll ----
SCROLL_REL_X = 1160
SCROLL_REL_Y = 500
SCROLL_CLICKS = 24
