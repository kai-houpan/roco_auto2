import time
import pyautogui

pyautogui.FAILSAFE = True

from config.settings import CLICK_WAIT, SCROLL_WAIT


def click(x: int, y: int, move_duration: float = 0.15) -> None:
    pyautogui.moveTo(x, y, duration=move_duration)
    pyautogui.click()
    time.sleep(CLICK_WAIT)


def scroll_at(x: int, y: int, clicks: int) -> None:
    pyautogui.moveTo(x, y, duration=0.15)
    pyautogui.scroll(-clicks)  # negative = scroll down
    time.sleep(SCROLL_WAIT)
