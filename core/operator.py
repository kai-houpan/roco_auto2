import ctypes
import os
import time

from config import settings as _cfg

# ---------------------------------------------------------------------------
# Interception constants
# ---------------------------------------------------------------------------
MOUSE_MOVE_ABSOLUTE = 0x0001
MOUSE_LEFT_DOWN      = 0x001
MOUSE_LEFT_UP        = 0x002
MOUSE_WHEEL          = 0x0400

# Interception 设备 ID：INTERCEPTION_MOUSE(0) = 11
MOUSE_DEVICE_ID = 11

# ---------------------------------------------------------------------------
# MouseStroke struct — must match Interception's InterceptionMouseStroke
# ---------------------------------------------------------------------------
class _MouseStroke(ctypes.Structure):
    _fields_ = [
        ("state",       ctypes.c_ushort),
        ("flags",       ctypes.c_ushort),
        ("rolling",     ctypes.c_short),
        ("x",           ctypes.c_int),
        ("y",           ctypes.c_int),
        ("information", ctypes.c_uint),
    ]

# ---------------------------------------------------------------------------
# Driver singleton — lazy-init on first mouse operation
# ---------------------------------------------------------------------------
_driver = None

class InterceptionDriver:
    """纯输出模式：只注入事件，不拦截物理鼠标。"""

    def __init__(self):
        dll_path = os.path.join(_cfg.ROOT, "interception.dll")
        try:
            self._dll = ctypes.WinDLL(dll_path)
        except OSError as e:
            if not os.path.exists(dll_path):
                msg = (
                    f"未找到 interception.dll (路径: {dll_path})。\n"
                    "请从 Interception 解压包的 library/x64/ 目录复制到项目根目录。\n"
                    "下载地址: https://github.com/oblitum/Interception/releases"
                )
            else:
                msg = (
                    f"interception.dll 加载失败，可能是缺少依赖库。\n"
                    f"文件位置: {dll_path}\n"
                    f"原始错误: {e}\n\n"
                    "请安装 Visual C++ 2015-2022 Redistributable (x64):\n"
                    "https://aka.ms/vs/17/release/vc_redist.x64.exe"
                )
            raise RuntimeError(msg)

        self._dll.interception_create_context.restype = ctypes.c_void_p
        self._dll.interception_send.argtypes = [
            ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_uint
        ]
        self._dll.interception_send.restype = ctypes.c_int

        self._context = self._dll.interception_create_context()
        if not self._context:
            raise RuntimeError("Interception 驱动上下文创建失败。请确认驱动已安装并重启电脑。")

    def move_to(self, x: int, y: int) -> None:
        stroke = _MouseStroke()
        stroke.flags = MOUSE_MOVE_ABSOLUTE
        stroke.x = int(x * 0xFFFF / _cfg.SCREEN_W)
        stroke.y = int(y * 0xFFFF / _cfg.SCREEN_H)
        self._dll.interception_send(self._context, MOUSE_DEVICE_ID, ctypes.byref(stroke), 1)

    def left_down(self) -> None:
        stroke = _MouseStroke()
        stroke.state = MOUSE_LEFT_DOWN
        self._dll.interception_send(self._context, MOUSE_DEVICE_ID, ctypes.byref(stroke), 1)

    def left_up(self) -> None:
        stroke = _MouseStroke()
        stroke.state = MOUSE_LEFT_UP
        self._dll.interception_send(self._context, MOUSE_DEVICE_ID, ctypes.byref(stroke), 1)

    def scroll(self, clicks: int) -> None:
        stroke = _MouseStroke()
        stroke.state = MOUSE_WHEEL
        stroke.rolling = clicks * _cfg.WHEEL_DELTA
        self._dll.interception_send(self._context, MOUSE_DEVICE_ID, ctypes.byref(stroke), 1)


def _get_driver() -> InterceptionDriver:
    global _driver
    if _driver is None:
        _driver = InterceptionDriver()
    return _driver


# ---------------------------------------------------------------------------
# Public API — identical signatures to the old PyAutoGUI version
# ---------------------------------------------------------------------------
def click(x: int, y: int, move_duration: float = 0.15) -> None:
    d = _get_driver()
    d.move_to(x, y)
    time.sleep(move_duration)
    d.left_down()
    time.sleep(_cfg.MOVE_DELAY)
    d.left_up()
    time.sleep(_cfg.CLICK_WAIT)


def scroll_at(x: int, y: int, clicks: int) -> None:
    d = _get_driver()
    d.move_to(x, y)
    time.sleep(_cfg.MOVE_DELAY)
    d.scroll(-clicks)  # negative = scroll down
    time.sleep(_cfg.SCROLL_WAIT)


def scroll_up_at(x: int, y: int, clicks: int) -> None:
    d = _get_driver()
    d.move_to(x, y)
    time.sleep(_cfg.MOVE_DELAY)
    d.scroll(clicks)  # positive = scroll up
    time.sleep(_cfg.SCROLL_WAIT)
