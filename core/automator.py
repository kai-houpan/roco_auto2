import time
import threading

from config import settings as _cfg
from config.dictionary_loader import EggEntry, GuluEntry
from core.recognizer import match_template, match_template_in_window
from core.operator import click, scroll_at, scroll_up_at
from core.window_manager import locate_window


class Automator:
    def __init__(self, egg_queue: list[EggEntry], gulu: GuluEntry,
                 log_cb, on_stopped_cb):
        self.egg_queue = egg_queue        # ordered list, never empty
        self.egg_index = 0
        self.gulu = gulu
        self.log = log_cb      # log_cb(level: str, message: str)
        self.on_stopped = on_stopped_cb

        self._stop_event = threading.Event()
        self._thread = None

        self.win_x = 0
        self.win_y = 0
        self.cycle_count = 0
        self._window_lost_count = 0
        self._poll_count = 0
        self._egg_scroll_total = 0

    def _current_egg(self) -> EggEntry:
        return self.egg_queue[self.egg_index]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def start(self) -> None:
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def _run(self) -> None:
        self.log("START", "工作流启动")
        try:
            if not self._state_1_locate_window():
                return

            self.cycle_count = 0
            while not self._stop_event.is_set():
                self.cycle_count += 1
                self._poll_count = 0
                self.log("START", f"第 {self.cycle_count} 轮循环开始")

                if not self._check_window():
                    return

                result = self._state_2()
                if result == "stop":
                    return
        except Exception as e:
            self.log("ERROR", f"未捕获异常: {e}")
            import traceback
            self.log("ERROR", traceback.format_exc())
        finally:
            self.log("STOP", "工作流结束")
            self.on_stopped()

    # ------------------------------------------------------------------
    # Window helpers
    # ------------------------------------------------------------------
    def _check_window(self) -> bool:
        if self._stop_event.is_set():
            return False
        pos = locate_window()
        if pos is None:
            self._window_lost_count += 1
            self.log("WARN", f"窗口定位失败 ({self._window_lost_count}/{_cfg.MAX_WINDOW_LOST_CHECKS})")
            if self._window_lost_count >= _cfg.MAX_WINDOW_LOST_CHECKS:
                self.log("STOP", "游戏窗口丢失，工作流停止，请检查游戏状态")
                return False
            time.sleep(_cfg.POLL_INTERVAL)
            return self._check_window()
        self._window_lost_count = 0
        wx, wy = pos
        if abs(wx - self.win_x) > 20 or abs(wy - self.win_y) > 20:
            self.log("WARN", f"窗口位置已更新: ({wx}, {wy})")
            self.win_x, self.win_y = wx, wy
        return True

    def _win_region(self) -> tuple[int, int, int, int]:
        return (self.win_x, self.win_y,
                self.win_x + _cfg.GAME_WINDOW_W, self.win_y + _cfg.GAME_WINDOW_H)

    def _window_center(self) -> tuple[int, int]:
        return self.win_x + _cfg.GAME_WINDOW_W // 2, self.win_y + _cfg.GAME_WINDOW_H // 2

    # ------------------------------------------------------------------
    # Reusable click-verify pattern
    # ------------------------------------------------------------------
    def _click_and_verify(self, target_img: str, verify_img: str,
                          target_dir: str, verify_dir: str,
                          max_retries: int = _cfg.MAX_CLICK_RETRIES) -> bool:
        """
        Find target_img, click it, verify that verify_img appears.
        Returns True on success, False if target not found or verification
        fails after max_retries.
        """
        region = self._win_region()
        for attempt in range(max_retries):
            if self._stop_event.is_set():
                return False
            pos = match_template(target_img, target_dir, region)
            if pos is None:
                self.log("FAIL", f"未找到 {target_img}")
                return False
            self.log("ACT", f"点击 {target_img} @ ({pos[0]}, {pos[1]})")
            click(pos[0], pos[1])

            verify_pos = match_template(verify_img, verify_dir, region)
            if verify_pos is not None:
                self.log("OK", f"验证 {verify_img} 成功")
                return True
            self.log("FAIL", f"验证 {verify_img} 失败 (第{attempt + 1}/{max_retries}次)")
        return False

    # ------------------------------------------------------------------
    # STATE_1 — Locate window
    # ------------------------------------------------------------------
    def _state_1_locate_window(self) -> bool:
        self.log("ACT", "正在定位游戏窗口...")
        pos = locate_window()
        if pos is None:
            self.log("STOP", "窗口未找到，工作流停止。请确认游戏已启动并处于孵蛋界面。")
            return False
        self.win_x, self.win_y = pos
        self.log("OK", f"窗口定位成功: ({self.win_x}, {self.win_y})")
        cx, cy = self._window_center()
        click(cx, cy)
        self.log("ACT", "点击窗口中心，确保获得焦点")
        return True

    # ------------------------------------------------------------------
    # STATE_2 — Check vacancy (noegg_selected)
    # ------------------------------------------------------------------
    def _state_2(self) -> str | None:
        if self._stop_event.is_set():
            return "stop"
        pos = match_template("noegg_selected.png", _cfg.DIAGRAM_DIR, self._win_region())
        if pos is not None:
            self.log("OK", "检测到孵蛋装置空缺 (noegg_selected)")
            self.log("ACT", f"点击 noegg_selected @ ({pos[0]}, {pos[1]})")
            click(pos[0], pos[1])
            if self._click_and_verify("putin.png", "putin_wait.png",
                                       _cfg.DIAGRAM_DIR, _cfg.DIAGRAM_DIR):
                return self._state_3()
            self.log("FAIL", "点击空缺装置后未出现 putin，重试 STATE_2")
            return self._state_2()
        return self._state_6()

    # ------------------------------------------------------------------
    # STATE_3 — Put in egg (putin)
    # ------------------------------------------------------------------
    def _state_3(self) -> str | None:
        if self._click_and_verify("putin.png", "putin_wait.png",
                                   _cfg.DIAGRAM_DIR, _cfg.DIAGRAM_DIR):
            return self._state_4()
        return self._state_2()

    # ------------------------------------------------------------------
    # STATE_4 — Select egg (with scroll)
    # ------------------------------------------------------------------
    def _state_4(self) -> str | None:
        egg = self._current_egg()
        egg_img = egg.image
        egg_sel = egg.selected
        for scroll_attempt in range(_cfg.MAX_SCROLL_RETRIES_EGG):
            if self._stop_event.is_set():
                return "stop"
            pos = match_template_in_window(
                egg_img, _cfg.EGGS_DIR,
                self.win_x, self.win_y, _cfg.GAME_WINDOW_W, _cfg.GAME_WINDOW_H,
                threshold=_cfg.MATCH_THRESHOLD_EGG)
            if pos is not None:
                self._egg_scroll_total = 0
                self.log("OK", f"找到蛋: {egg.name} ({egg_img})")
                self.log("ACT", f"点击 {egg_img} @ ({pos[0]}, {pos[1]})")
                click(pos[0], pos[1])
                sel_pos = match_template_in_window(
                    egg_sel, _cfg.EGGS_DIR,
                    self.win_x, self.win_y, _cfg.GAME_WINDOW_W, _cfg.GAME_WINDOW_H,
                    threshold=_cfg.MATCH_THRESHOLD_EGG)
                if sel_pos is not None:
                    self.log("OK", f"蛋已选中: {egg_sel}")
                    return self._state_5()
                self.log("FAIL", f"蛋选中验证失败: {egg_sel}")
                continue
            sx = self.win_x + _cfg.SCROLL_REL_X
            sy = self.win_y + _cfg.SCROLL_REL_Y
            self.log("SCROLL", f"滚动蛋列表 ({scroll_attempt + 1}/{_cfg.MAX_SCROLL_RETRIES_EGG})")
            scroll_at(sx, sy, _cfg.SCROLL_CLICKS)
            self._egg_scroll_total += 1

        self.log("FAIL", f"未找到目标蛋 {egg.name}，尝试下一个")
        self._rollback_egg_list()
        self.egg_index += 1
        if self.egg_index < len(self.egg_queue):
            next_egg = self._current_egg()
            self.log("ACT", f"切换蛋种: {next_egg.name}")
            return self._state_4()
        self.log("STOP", "队列中所有蛋种均已耗尽")
        return "stop"

    def _rollback_egg_list(self) -> None:
        if self._egg_scroll_total == 0:
            return
        self.log("SCROLL", f"回滚蛋列表: {self._egg_scroll_total} 次")
        sx = self.win_x + _cfg.SCROLL_REL_X
        sy = self.win_y + _cfg.SCROLL_REL_Y
        for _ in range(self._egg_scroll_total):
            if self._stop_event.is_set():
                return
            scroll_up_at(sx, sy, _cfg.SCROLL_CLICKS)
        self._egg_scroll_total = 0

    # ------------------------------------------------------------------
    # STATE_5 — Confirm put-in (putin_1 → takeout)
    # ------------------------------------------------------------------
    def _state_5(self) -> str | None:
        region = self._win_region()
        for attempt in range(_cfg.MAX_CLICK_RETRIES):
            if self._stop_event.is_set():
                return "stop"
            pos = match_template("putin_1.png", _cfg.DIAGRAM_DIR, region)
            if pos is None:
                self.log("FAIL", "未找到 putin_1.png")
                return self._state_4()
            self.log("ACT", f"点击 putin_1 @ ({pos[0]}, {pos[1]})")
            click(pos[0], pos[1])
            time.sleep(_cfg.DELAY_PUTIN_VERIFY)
            verify_pos = match_template("takeout.png", _cfg.DIAGRAM_DIR, region)
            if verify_pos is not None:
                self.log("OK", "蛋放入确认成功")
                self.egg_index = 0
                self._egg_scroll_total = 0
                return self._state_2()
            self.log("FAIL", f"takeout 验证失败 (第{attempt + 1}/{_cfg.MAX_CLICK_RETRIES}次)")
        self.log("FAIL", "putin_1 验证失败，回到选蛋")
        return self._state_4()

    # ------------------------------------------------------------------
    # STATE_6 — Unselected vacancy (noegg_notselected)
    # ------------------------------------------------------------------
    def _state_6(self) -> str | None:
        if self._stop_event.is_set():
            return "stop"
        pos = match_template("noegg_notselected.png", _cfg.DIAGRAM_DIR, self._win_region())
        if pos is not None:
            self.log("OK", "检测到未选中空缺 (noegg_notselected)")
            self.log("ACT", f"点击 noegg_notselected @ ({pos[0]}, {pos[1]})")
            click(pos[0], pos[1])
            verify = match_template("noegg_selected.png", _cfg.DIAGRAM_DIR, self._win_region())
            if verify is not None:
                self.log("OK", "验证 noegg_selected 成功")
                return self._state_2()
            self.log("FAIL", "点击后未出现 noegg_selected，重试")
            return self._state_6()
        return self._state_7()

    # ------------------------------------------------------------------
    # STATE_7 — Poll for hatching completion (iterative, no recursion)
    # ------------------------------------------------------------------
    def _state_7(self) -> str | None:
        while not self._stop_event.is_set():
            # Check finished_selected
            pos = match_template("finished_selected.png", _cfg.DIAGRAM_DIR, self._win_region())
            if pos is not None:
                self._poll_count = 0
                self.log("OK", "检测到孵化完成 (finished_selected)")
                self.log("ACT", f"点击 finished_selected @ ({pos[0]}, {pos[1]})")
                click(pos[0], pos[1])
                if self._click_and_verify("contract.png", "contract_wait.png",
                                           _cfg.DIAGRAM_DIR, _cfg.DIAGRAM_DIR):
                    return self._state_8()
                self.log("FAIL", "contract 验证失败，继续轮询")
                continue

            # Check finished_notselected
            pos = match_template("finished_notselected.png", _cfg.DIAGRAM_DIR, self._win_region())
            if pos is not None:
                self._poll_count = 0
                self.log("OK", "检测到未选中完成 (finished_notselected)")
                self.log("ACT", f"点击 finished_notselected @ ({pos[0]}, {pos[1]})")
                click(pos[0], pos[1])
                verify = match_template("finished_selected.png", _cfg.DIAGRAM_DIR, self._win_region())
                if verify is not None:
                    self.log("OK", "验证 finished_selected 成功")
                    return self._state_8()
                self.log("FAIL", "验证 finished_selected 失败，继续轮询")
                continue

            # Neither found — wait
            if self._poll_count == 0:
                self.log("ACT", "开始等待孵化中...")
            self._poll_count += 1
            if self._poll_count % 20 == 0:
                self.log("ACT", f"等待孵化中... (已轮询 {self._poll_count} 次)")
            time.sleep(_cfg.POLL_INTERVAL)

        return "stop"

    # ------------------------------------------------------------------
    # STATE_8 — Contract entry (contract)
    # ------------------------------------------------------------------
    def _state_8(self) -> str | None:
        if self._click_and_verify("contract.png", "contract_wait.png",
                                   _cfg.DIAGRAM_DIR, _cfg.DIAGRAM_DIR):
            return self._state_9()
        return self._state_7()

    # ------------------------------------------------------------------
    # STATE_9 — Select gulu (with scroll)
    # ------------------------------------------------------------------
    def _state_9(self) -> str | None:
        gulu_img = self.gulu.image
        gulu_sel = self.gulu.selected
        for scroll_attempt in range(_cfg.MAX_SCROLL_RETRIES):
            if self._stop_event.is_set():
                return "stop"
            pos = match_template_in_window(
                gulu_img, _cfg.GULUS_DIR,
                self.win_x, self.win_y, _cfg.GAME_WINDOW_W, _cfg.GAME_WINDOW_H)
            if pos is not None:
                self.log("OK", f"找到咕噜球: {self.gulu.name} ({gulu_img})")
                self.log("ACT", f"点击 {gulu_img} @ ({pos[0]}, {pos[1]})")
                click(pos[0], pos[1])
                sel_pos = match_template_in_window(
                    gulu_sel, _cfg.GULUS_DIR,
                    self.win_x, self.win_y, _cfg.GAME_WINDOW_W, _cfg.GAME_WINDOW_H)
                if sel_pos is not None:
                    self.log("OK", f"咕噜球已选中: {gulu_sel}")
                    return self._state_10()
                self.log("FAIL", f"咕噜球选中验证失败: {gulu_sel}")
                continue
            sx = self.win_x + _cfg.SCROLL_REL_X
            sy = self.win_y + _cfg.SCROLL_REL_Y
            self.log("SCROLL", f"滚动咕噜球列表 ({scroll_attempt + 1}/{_cfg.MAX_SCROLL_RETRIES})")
            scroll_at(sx, sy, _cfg.SCROLL_CLICKS)
        self.log("STOP", f"未找到目标咕噜球 {self.gulu.name} (重试耗尽)")
        return "stop"

    # ------------------------------------------------------------------
    # STATE_10 — Confirm contract (contract_1, animate ~5s → click.png)
    # ------------------------------------------------------------------
    def _state_10(self) -> str | None:
        region = self._win_region()
        for anim_attempt in range(_cfg.MAX_ANIMATION_RETRIES):
            if self._stop_event.is_set():
                return "stop"
            pos = match_template("contract_1.png", _cfg.DIAGRAM_DIR, region)
            if pos is None:
                self.log("FAIL", "未找到 contract_1.png")
                return self._state_9()
            self.log("ACT", f"点击 contract_1 @ ({pos[0]}, {pos[1]})")
            click(pos[0], pos[1])

            self.log("ACT", f"等待契约动画 (最长 {_cfg.ANIMATION_TIMEOUT}s)...")
            elapsed = 0.0
            while elapsed < _cfg.ANIMATION_TIMEOUT:
                if self._stop_event.is_set():
                    return "stop"
                verify_pos = match_template("click.png", _cfg.DIAGRAM_DIR, region)
                if verify_pos is not None:
                    self.log("OK", f"click.png 出现 (等待 {elapsed:.1f}s)")
                    return self._state_11()
                time.sleep(_cfg.ANIMATION_POLL_INTERVAL)
                elapsed += _cfg.ANIMATION_POLL_INTERVAL

            self.log("FAIL", f"动画等待超时 (第{anim_attempt + 1}/{_cfg.MAX_ANIMATION_RETRIES}次)")
        self.log("FAIL", "contract_1 动画等待全部超时，回到 STATE_9")
        return self._state_9()

    # ------------------------------------------------------------------
    # STATE_11 — Final confirm (click → site)
    # ------------------------------------------------------------------
    def _state_11(self) -> str | None:
        for attempt in range(_cfg.MAX_CLICK_RETRIES):
            if self._stop_event.is_set():
                return "stop"
            cx = self.win_x + _cfg.STATE11_OFFSET_X
            cy = self.win_y + _cfg.STATE11_OFFSET_Y
            self.log("ACT", f"点击固定位置 @ ({cx}, {cy})")
            click(cx, cy)
            time.sleep(_cfg.DELAY_SITE_VERIFY)
            verify_pos = match_template("site.png", _cfg.DIAGRAM_DIR, self._win_region())
            if verify_pos is not None:
                self.log("OK", "契约完成 (site 验证成功)")
                return self._state_2()
            self.log("FAIL", f"site 验证失败 (第{attempt + 1}/{_cfg.MAX_CLICK_RETRIES}次)")
        self.log("STOP", "site 验证失败 (重试耗尽)")
        return "stop"

