import tkinter as tk
from tkinter import ttk, messagebox
import os
import time
import threading
import webbrowser

from config import settings as _cfg
from config.dictionary_loader import load_eggs, load_gulus, EggEntry, GuluEntry
from core.automator import Automator
from ui.control_panel import ControlPanel
from ui.log_panel import LogPanel


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("洛克王国自动孵蛋工具")
        self.root.geometry("500x650")
        self.root.configure(bg="white")
        self.root.minsize(400, 500)

        self.ACCENT = "#112DA5"  # rgb(17, 45, 165)
        self._style()
        self._load_dictionaries()
        self._create_widgets()

        self.automator: Automator | None = None
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _style(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(".", background="white", foreground="black",
                         fieldbackground="white")
        style.configure("TLabel", background="white", foreground="black")
        style.configure("TFrame", background="white")

        # Buttons — white with visible border
        style.configure("TButton", background="white", foreground="black",
                         borderwidth=2, relief="raised")
        style.map("TButton",
                  background=[("active", "#E8E8E8"), ("disabled", "#F5F5F5")],
                  relief=[("pressed", "sunken")])

        # Combobox
        style.configure("TCombobox",
                        fieldbackground="white", background="white",
                        foreground="black", arrowcolor=self.ACCENT)
        style.map("TCombobox",
                  fieldbackground=[("readonly", "white")],
                  selectbackground=[("readonly", self.ACCENT)],
                  selectforeground=[("readonly", "white")])

    def _load_dictionaries(self):
        try:
            self.eggs = load_eggs(_cfg.EGGS_DICT_FILE, _cfg.EGGS_DIR)
            self.gulus = load_gulus(_cfg.GULUS_DICT_FILE, _cfg.GULUS_DIR)
        except (FileNotFoundError, ValueError) as e:
            messagebox.showerror("启动失败", str(e))
            raise SystemExit(str(e))

    def _create_widgets(self):
        # Title
        title = ttk.Label(self.root, text="洛克王国自动孵蛋工具",
                          font=("", 14, "bold"))
        title.pack(pady=(10, 6))

        # Control panel
        config_names = list(_cfg.SCREEN_CONFIGS.keys())
        egg_names = [e.name for e in self.eggs]
        gulu_names = [g.name for g in self.gulus]
        self.control = ControlPanel(
            self.root, egg_names, gulu_names, config_names,
            on_start=self._on_start, on_stop=self._on_stop,
            on_test=self._on_test_match, on_config_change=self._on_config_change)
        self.control.pack(fill=tk.X, padx=10, pady=(0, 6))

        # Footer (pack before LogPanel so it claims space first)
        footer_frame = ttk.Frame(self.root)
        footer_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0, 4))

        credit_left = ttk.Label(footer_frame, text="本程序由 ")
        credit_left.pack(side=tk.LEFT)

        credit_name = tk.Label(
            footer_frame, text="余耳Yure",
            fg="#022DAC", font=("", 9), cursor="hand2",
            background="white")
        credit_name.pack(side=tk.LEFT)
        credit_name.bind("<Button-1>",
                         lambda e: webbrowser.open("https://space.bilibili.com/3546812698855825"))

        credit_right = ttk.Label(footer_frame, text=" 开发  |  日志文件: logs/")
        credit_right.pack(side=tk.LEFT)

        # Log panel
        self.log_panel = LogPanel(self.root)
        self.log_panel.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 6))

    # ------------------------------------------------------------------
    # Thread-safe logging
    # ------------------------------------------------------------------
    def _log(self, level: str, message: str):
        method = getattr(self.log_panel, level.lower(), self.log_panel.ok)
        self.root.after(0, method, message)

    # ------------------------------------------------------------------
    # Start / Stop
    # ------------------------------------------------------------------
    def _on_start(self, egg_names: list[str], gulu_name: str):
        eggs = [next((e for e in self.eggs if e.name == n), None) for n in egg_names]
        if any(e is None for e in eggs):
            messagebox.showerror("错误", "队列中包含无效蛋种")
            return
        gulu = next((g for g in self.gulus if g.name == gulu_name), None)
        if gulu is None:
            messagebox.showerror("错误", "请选择有效的咕噜球")
            return

        self.control.set_running(True)
        self.automator = Automator(eggs, gulu, self._log, self._on_automator_stopped)
        self.automator.start()

    def _on_stop(self):
        if self.automator and self.automator.is_running():
            self._log("WARN", "用户请求停止...")
            self.automator.stop()

    def _on_test_match(self):
        from core.recognizer import match_template_raw

        self._log("START", "=== 开始匹配度测试 ===")

        templates = []

        # All diagram PNGs
        if os.path.isdir(_cfg.DIAGRAM_DIR):
            for f in sorted(os.listdir(_cfg.DIAGRAM_DIR)):
                if f.lower().endswith(".png"):
                    templates.append((f, _cfg.DIAGRAM_DIR))

        # Selected egg
        egg_name = self.control.selected_egg_name()
        egg = next((e for e in self.eggs if e.name == egg_name), None)
        if egg is not None:
            templates.append((egg.image, _cfg.EGGS_DIR))
            templates.append((egg.selected, _cfg.EGGS_DIR))

        # Selected gulu
        gulu_name = self.control.selected_gulu_name()
        gulu = next((g for g in self.gulus if g.name == gulu_name), None)
        if gulu is not None:
            templates.append((gulu.image, _cfg.GULUS_DIR))
            templates.append((gulu.selected, _cfg.GULUS_DIR))

        results = []
        for name, directory in templates:
            try:
                cx, cy, conf = match_template_raw(name, directory)
                results.append((name, conf, cx, cy))
            except FileNotFoundError:
                self._log("FAIL", f"文件不存在: {directory}/{name}")

        results.sort(key=lambda r: r[1], reverse=True)

        for name, conf, cx, cy in results:
            if conf >= _cfg.MATCH_THRESHOLD:
                tag = "OK"
            elif conf >= _cfg.WINDOW_MATCH_THRESHOLD:
                tag = "WARN"
            else:
                tag = "FAIL"
            self._log(tag, f"{name}: {conf:.4f} — ({cx}, {cy})")

        self._log("START", "=== 匹配度测试完成 ===")

    def _on_config_change(self, name: str):
        if not _cfg.activate_config(name):
            return
        self._load_dictionaries()
        egg_names = [e.name for e in self.eggs]
        gulu_names = [g.name for g in self.gulus]
        self.control.refresh_dictionaries(egg_names, gulu_names)
        self._log("START", f"屏幕设置已切换: {name}")

    def _on_automator_stopped(self):
        self.root.after(0, self._handle_stopped)

    def _handle_stopped(self):
        self.control.set_running(False)
        self._dump_log_to_file()
        if self.control.auto_close_var.get():
            threading.Thread(target=self._do_auto_close, daemon=True).start()
        if self.control.auto_shutdown_var.get():
            self._do_auto_shutdown()

    def _do_auto_close(self):
        from core.operator import click
        from core.window_manager import locate_window
        if self.automator is None:
            return
        wx, wy = self.automator.win_x, self.automator.win_y
        cx, cy = wx + _cfg.CLOSE_OFFSET_X, wy + _cfg.CLOSE_OFFSET_Y
        self._log("ACT", f"自动关闭游戏窗口: ({cx}, {cy})")
        click(cx, cy)
        for _ in range(30):
            time.sleep(0.5)
            if locate_window() is None:
                self._log("OK", "游戏窗口已关闭")
                return
        self._log("WARN", "未能确认游戏窗口关闭")

    def _do_auto_shutdown(self):
        self._log("WARN", "系统将在 60 秒后关机，如需取消请运行: shutdown /a")
        os.system("shutdown /s /t 60")

    def _dump_log_to_file(self):
        from datetime import datetime
        text = self.log_panel.dump_text()
        if not text:
            return
        os.makedirs(_cfg.LOGS_DIR, exist_ok=True)
        filename = datetime.now().strftime("%Y%m%d_%H%M%S") + ".log"
        filepath = os.path.join(_cfg.LOGS_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(text)
        self._log("START", f"日志已保存: {filepath}")

    def _on_close(self):
        if self.automator and self.automator.is_running():
            self.automator.stop()
            self.automator._thread.join(timeout=2)
        self.root.destroy()

    def run(self):
        self.root.mainloop()
