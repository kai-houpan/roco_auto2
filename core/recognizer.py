import cv2
import numpy as np
from PIL import ImageGrab

from config.settings import MATCH_THRESHOLD


def _grab_screen(region: tuple[int, int, int, int] | None = None):
    img = ImageGrab.grab(bbox=region, all_screens=True)
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)


def match_template(
    template_name: str,
    template_dir: str,
    region: tuple[int, int, int, int] | None = None,
    threshold: float = MATCH_THRESHOLD,
) -> tuple[int, int] | None:
    """
    Full-screen (or region) template matching.
    Returns (center_x, center_y) of the best match, or None.
    """
    template_path = f"{template_dir}/{template_name}"
    template = cv2.imread(template_path)
    if template is None:
        raise FileNotFoundError(f"无法读取模板图像: {template_path}")

    screen = _grab_screen(region)

    result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    if max_val < threshold:
        return None

    h, w = template.shape[:2]
    if region:
        offset_x, offset_y = region[0], region[1]
    else:
        offset_x, offset_y = 0, 0

    center_x = max_loc[0] + offset_x + w // 2
    center_y = max_loc[1] + offset_y + h // 2
    return center_x, center_y


def match_template_in_window(
    template_name: str,
    template_dir: str,
    win_x: int,
    win_y: int,
    win_w: int,
    win_h: int,
    threshold: float = MATCH_THRESHOLD,
) -> tuple[int, int] | None:
    """Template matching constrained to the game window region."""
    region = (win_x, win_y, win_x + win_w, win_y + win_h)
    return match_template(template_name, template_dir, region, threshold)
