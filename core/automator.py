import time
import threading

from config.settings import (
    DIAGRAM_DIR, EGGS_DIR, GULUS_DIR,
    GAME_WINDOW_W, GAME_WINDOW_H,
    POLL_INTERVAL, ANIMATION_POLL_INTERVAL, ANIMATION_TIMEOUT,
    MAX_CLICK_RETRIES, MAX_SCROLL_RETRIES, MAX_WINDOW_LOST_CHECKS,
    MAX_ANIMATION_RETRIES,
    SCROLL_REL_X, SCROLL_REL_Y, SCROLL_CLICKS,
)
from config.dictionary_loader import EggEntry, GuluEntry
from core.recognizer import match_template, match_template_in_window
from core.operator import click, scroll_at
from core.window_manager import locate_window


class Automator:
    def __init__(self, egg: EggEntry, gulu: GuluEntry,
                 log_cb, on_stopped_cb):
        self.egg = egg
        self.gulu = gulu
        self.log = log_cb      # log_cb(level: str, message: str)
        self.on_stopped = on_stopped_cb

        self._stop_event = threading.Event()
        self._thread = None

        self.win_x = 0
        self.win_y = 0
        self.cycle_count = 0
        self._window_lost_count = 0

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
            self.log("WARN", f"窗口定位失败 ({self._window_lost_count}/{MAX_WINDOW_LOST_CHECKS})")
            if self._window_lost_count >= MAX_WINDOW_LOST_CHECKS:
                self.log("STOP", "游戏窗口丢失，工作流停止，请检查游戏状态")
                return False
            time.sleep(POLL_INTERVAL)
            return self._check_window()
        self._window_lost_count = 0
        wx, wy = pos
        if abs(wx - self.win_x) > 20 or abs(wy - self.win_y) > 20:
            self.log("WARN", f"窗口位置已更新: ({wx}, {wy})")
            self.win_x, self.win_y = wx, wy
        return True

    def _win_region(self) -> tuple[int, int, int, int]:
        return (self.win_x, self.win_y,
                self.win_x + GAME_WINDOW_W, self.win_y + GAME_WINDOW_H)

    def _window_center(self) -> tuple[int, int]:
        return self.win_x + GAME_WINDOW_W // 2, self.win_y + GAME_WINDOW_H // 2

    # ------------------------------------------------------------------
    # Reusable click-verify pattern
    # ------------------------------------------------------------------
    def _click_and_verify(self, target_img: str, verify_img: str,
                          target_dir: str, verify_dir: str,
                          max_retries: int = MAX_CLICK_RETRIES) -> bool:
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
        pos = match_template("noegg_selected.png", DIAGRAM_DIR, self._win_region())
        if pos is not None:
            self.log("OK", "检测到孵蛋装置空缺 (noegg_selected)")
            self.log("ACT", f"点击 noegg_selected @ ({pos[0]}, {pos[1]})")
            click(pos[0], pos[1])
            if self._click_and_verify("putin.png", "putin_wait.png",
                                       DIAGRAM_DIR, DIAGRAM_DIR):
                return self._state_3()
            self.log("FAIL", "点击空缺装置后未出现 putin，重试 STATE_2")
            return self._state_2()
        return self._state_6()

    # ------------------------------------------------------------------
    # STATE_3 — Put in egg (putin)
    # ------------------------------------------------------------------
    def _state_3(self) -> str | None:
        if self._click_and_verify("putin.png", "putin_wait.png",
                                   DIAGRAM_DIR, DIAGRAM_DIR):
            return self._state_4()
        return self._state_2()

    # ------------------------------------------------------------------
    # STATE_4 — Select egg (with scroll)
    # ------------------------------------------------------------------
    def _state_4(self) -> str | None:
        egg_img = self.egg.image
        egg_sel = self.egg.selected
        for scroll_attempt in range(MAX_SCROLL_RETRIES):
            if self._stop_event.is_set():
                return "stop"
            pos = match_template_in_window(
                egg_img, EGGS_DIR,
                self.win_x, self.win_y, GAME_WINDOW_W, GAME_WINDOW_H)
            if pos is not None:
                self.log("OK", f"找到蛋: {self.egg.name} ({egg_img})")
                self.log("ACT", f"点击 {egg_img} @ ({pos[0]}, {pos[1]})")
                click(pos[0], pos[1])
                sel_pos = match_template_in_window(
                    egg_sel, EGGS_DIR,
                    self.win_x, self.win_y, GAME_WINDOW_W, GAME_WINDOW_H)
                if sel_pos is not None:
                    self.log("OK", f"蛋已选中: {egg_sel}")
                    return self._state_5()
                self.log("FAIL", f"蛋选中验证失败: {egg_sel}")
                continue
            sx = self.win_x + SCROLL_REL_X
            sy = self.win_y + SCROLL_REL_Y
            self.log("SCROLL", f"滚动蛋列表 ({scroll_attempt + 1}/{MAX_SCROLL_RETRIES})")
            scroll_at(sx, sy, SCROLL_CLICKS)
        self.log("STOP", f"未找到目标蛋 {self.egg.name} (重试耗尽)")
        return "stop"

    # ------------------------------------------------------------------
    # STATE_5 — Confirm put-in (putin_1 → takeout)
    # ------------------------------------------------------------------
    def _state_5(self) -> str | None:
        if self._click_and_verify("putin_1.png", "takeout.png",
                                   DIAGRAM_DIR, DIAGRAM_DIR):
            self.log("OK", "蛋放入确认成功")
            return self._state_2()
        self.log("FAIL", "putin_1 验证失败，回到选蛋")
        return self._state_4()

    # ------------------------------------------------------------------
    # STATE_6 — Unselected vacancy (noegg_notselected)
    # ------------------------------------------------------------------
    def _state_6(self) -> str | None:
        if self._stop_event.is_set():
            return "stop"
        pos = match_template("noegg_notselected.png", DIAGRAM_DIR, self._win_region())
        if pos is not None:
            self.log("OK", "检测到未选中空缺 (noegg_notselected)")
            self.log("ACT", f"点击 noegg_notselected @ ({pos[0]}, {pos[1]})")
            click(pos[0], pos[1])
            verify = match_template("noegg_selected.png", DIAGRAM_DIR, self._win_region())
            if verify is not None:
                self.log("OK", "验证 noegg_selected 成功")
                return self._state_2()
            self.log("FAIL", "点击后未出现 noegg_selected，重试")
            return self._state_6()
        return self._state_7()

    # ------------------------------------------------------------------
    # STATE_7 — Check finished (finished_selected)
    # ------------------------------------------------------------------
    def _state_7(self) -> str | None:
        if self._stop_event.is_set():
            return "stop"
        pos = match_template("finished_selected.png", DIAGRAM_DIR, self._win_region())
        if pos is not None:
            self.log("OK", "检测到孵化完成 (finished_selected)")
            self.log("ACT", f"点击 finished_selected @ ({pos[0]}, {pos[1]})")
            click(pos[0], pos[1])
            if self._click_and_verify("contract.png", "contract_wait.png",
                                       DIAGRAM_DIR, DIAGRAM_DIR):
                return self._state_8()
            self.log("FAIL", "contract 验证失败，回到 STATE_7")
            return self._state_7()
        return self._state_12()

    # ------------------------------------------------------------------
    # STATE_8 — Contract entry (contract)
    # ------------------------------------------------------------------
    def _state_8(self) -> str | None:
        if self._click_and_verify("contract.png", "contract_wait.png",
                                   DIAGRAM_DIR, DIAGRAM_DIR):
            return self._state_9()
        return self._state_7()

    # ------------------------------------------------------------------
    # STATE_9 — Select gulu (with scroll)
    # ------------------------------------------------------------------
    def _state_9(self) -> str | None:
        gulu_img = self.gulu.image
        gulu_sel = self.gulu.selected
        for scroll_attempt in range(MAX_SCROLL_RETRIES):
            if self._stop_event.is_set():
                return "stop"
            pos = match_template_in_window(
                gulu_img, GULUS_DIR,
                self.win_x, self.win_y, GAME_WINDOW_W, GAME_WINDOW_H)
            if pos is not None:
                self.log("OK", f"找到咕噜球: {self.gulu.name} ({gulu_img})")
                self.log("ACT", f"点击 {gulu_img} @ ({pos[0]}, {pos[1]})")
                click(pos[0], pos[1])
                sel_pos = match_template_in_window(
                    gulu_sel, GULUS_DIR,
                    self.win_x, self.win_y, GAME_WINDOW_W, GAME_WINDOW_H)
                if sel_pos is not None:
                    self.log("OK", f"咕噜球已选中: {gulu_sel}")
                    return self._state_10()
                self.log("FAIL", f"咕噜球选中验证失败: {gulu_sel}")
                continue
            sx = self.win_x + SCROLL_REL_X
            sy = self.win_y + SCROLL_REL_Y
            self.log("SCROLL", f"滚动咕噜球列表 ({scroll_attempt + 1}/{MAX_SCROLL_RETRIES})")
            scroll_at(sx, sy, SCROLL_CLICKS)
        self.log("STOP", f"未找到目标咕噜球 {self.gulu.name} (重试耗尽)")
        return "stop"

    # ------------------------------------------------------------------
    # STATE_10 — Confirm contract (contract_1, animate ~5s → click.png)
    # ------------------------------------------------------------------
    def _state_10(self) -> str | None:
        region = self._win_region()
        for anim_attempt in range(MAX_ANIMATION_RETRIES):
            if self._stop_event.is_set():
                return "stop"
            pos = match_template("contract_1.png", DIAGRAM_DIR, region)
            if pos is None:
                self.log("FAIL", "未找到 contract_1.png")
                return self._state_9()
            self.log("ACT", f"点击 contract_1 @ ({pos[0]}, {pos[1]})")
            click(pos[0], pos[1])

            self.log("ACT", f"等待契约动画 (最长 {ANIMATION_TIMEOUT}s)...")
            elapsed = 0.0
            while elapsed < ANIMATION_TIMEOUT:
                if self._stop_event.is_set():
                    return "stop"
                verify_pos = match_template("click.png", DIAGRAM_DIR, region)
                if verify_pos is not None:
                    self.log("OK", f"click.png 出现 (等待 {elapsed:.1f}s)")
                    return self._state_11()
                time.sleep(ANIMATION_POLL_INTERVAL)
                elapsed += ANIMATION_POLL_INTERVAL

            self.log("FAIL", f"动画等待超时 (第{anim_attempt + 1}/{MAX_ANIMATION_RETRIES}次)")
        self.log("FAIL", "contract_1 动画等待全部超时，回到 STATE_9")
        return self._state_9()

    # ------------------------------------------------------------------
    # STATE_11 — Final confirm (click → site)
    # ------------------------------------------------------------------
    def _state_11(self) -> str | None:
        for attempt in range(MAX_CLICK_RETRIES):
            if self._stop_event.is_set():
                return "stop"
            pos = match_template("click.png", DIAGRAM_DIR, self._win_region())
            if pos is None:
                self.log("FAIL", "未找到 click.png")
                time.sleep(POLL_INTERVAL)
                continue
            self.log("ACT", f"点击 click @ ({pos[0]}, {pos[1]})")
            click(pos[0], pos[1])
            verify_pos = match_template("site.png", DIAGRAM_DIR, self._win_region())
            if verify_pos is not None:
                self.log("OK", "契约完成 (site 验证成功)")
                return self._state_2()
            self.log("FAIL", f"site 验证失败 (第{attempt + 1}/{MAX_CLICK_RETRIES}次)")
        self.log("STOP", "click/site 验证失败 (重试耗尽)")
        return "stop"

    # ------------------------------------------------------------------
    # STATE_12 — Unselected finished (finished_notselected)
    # ------------------------------------------------------------------
    def _state_12(self) -> str | None:
        if self._stop_event.is_set():
            return "stop"
        pos = match_template("finished_notselected.png", DIAGRAM_DIR, self._win_region())
        if pos is not None:
            self.log("OK", "检测到未选中完成 (finished_notselected)")
            self.log("ACT", f"点击 finished_notselected @ ({pos[0]}, {pos[1]})")
            click(pos[0], pos[1])
            verify = match_template("finished_selected.png", DIAGRAM_DIR, self._win_region())
            if verify is not None:
                self.log("OK", "验证 finished_selected 成功")
                return self._state_8()
            self.log("FAIL", "验证 finished_selected 失败，重试")
            return self._state_12()
        time.sleep(POLL_INTERVAL)
        return self._state_7()
