import tkinter as tk
from tkinter import ttk, messagebox
import os

from config.settings import EGGS_DICT_FILE, GULUS_DICT_FILE, EGGS_DIR, GULUS_DIR
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
            self.eggs = load_eggs(EGGS_DICT_FILE, EGGS_DIR)
            self.gulus = load_gulus(GULUS_DICT_FILE, GULUS_DIR)
        except (FileNotFoundError, ValueError) as e:
            messagebox.showerror("启动失败", str(e))
            raise SystemExit(str(e))

    def _create_widgets(self):
        # Title
        title = ttk.Label(self.root, text="洛克王国自动孵蛋工具",
                          font=("", 14, "bold"))
        title.pack(pady=(10, 6))

        # Control panel
        egg_names = [e.name for e in self.eggs]
        gulu_names = [g.name for g in self.gulus]
        self.control = ControlPanel(
            self.root, egg_names, gulu_names,
            on_start=self._on_start, on_stop=self._on_stop)
        self.control.pack(fill=tk.X, padx=10, pady=(0, 6))

        # Log panel
        self.log_panel = LogPanel(self.root)
        self.log_panel.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 6))

        # Footer
        footer = ttk.Label(self.root, text="日志文件: logs/")
        footer.pack(side=tk.BOTTOM, pady=(0, 4))

    # ------------------------------------------------------------------
    # Thread-safe logging
    # ------------------------------------------------------------------
    def _log(self, level: str, message: str):
        method = getattr(self.log_panel, level.lower(), self.log_panel.ok)
        self.root.after(0, method, message)

    # ------------------------------------------------------------------
    # Start / Stop
    # ------------------------------------------------------------------
    def _on_start(self, egg_name: str, gulu_name: str):
        egg = next((e for e in self.eggs if e.name == egg_name), None)
        gulu = next((g for g in self.gulus if g.name == gulu_name), None)
        if egg is None or gulu is None:
            messagebox.showerror("错误", "请选择有效的蛋和咕噜球")
            return

        self.control.set_running(True)
        self.automator = Automator(egg, gulu, self._log, self._on_automator_stopped)
        self.automator.start()

    def _on_stop(self):
        if self.automator and self.automator.is_running():
            self._log("WARN", "用户请求停止...")
            self.automator.stop()

    def _on_automator_stopped(self):
        self.root.after(0, self._handle_stopped)

    def _handle_stopped(self):
        self.control.set_running(False)

    def _on_close(self):
        if self.automator and self.automator.is_running():
            self.automator.stop()
            self.automator._thread.join(timeout=2)
        self.root.destroy()

    def run(self):
        self.root.mainloop()
