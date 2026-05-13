import tkinter as tk
from tkinter import ttk


class ControlPanel(ttk.Frame):
    def __init__(self, parent, egg_names: list[str], gulu_names: list[str],
                 on_start, on_stop):
        super().__init__(parent)
        self.egg_names = egg_names
        self.gulu_names = gulu_names
        self._on_start = on_start
        self._on_stop = on_stop
        self._running = False
        self._create_widgets()

    def _create_widgets(self):
        # Egg selection
        ttk.Label(self, text="选择目标蛋:").grid(
            row=0, column=0, sticky="w", padx=4, pady=(6, 2))
        self.egg_var = tk.StringVar(value=self.egg_names[0] if self.egg_names else "")
        self.egg_combo = ttk.Combobox(
            self, textvariable=self.egg_var, values=self.egg_names, state="readonly")
        self.egg_combo.grid(row=1, column=0, sticky="ew", padx=4, pady=(0, 4))

        # Gulu selection
        ttk.Label(self, text="选择咕噜球:").grid(
            row=2, column=0, sticky="w", padx=4, pady=(6, 2))
        self.gulu_var = tk.StringVar(value=self.gulu_names[0] if self.gulu_names else "")
        self.gulu_combo = ttk.Combobox(
            self, textvariable=self.gulu_var, values=self.gulu_names, state="readonly")
        self.gulu_combo.grid(row=3, column=0, sticky="ew", padx=4, pady=(0, 4))

        # Buttons
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=4, column=0, pady=(8, 4))

        self.start_btn = ttk.Button(btn_frame, text="▶ 启动", command=self._do_start)
        self.start_btn.pack(side=tk.LEFT, padx=4)

        self.stop_btn = ttk.Button(btn_frame, text="⏹ 停止", command=self._do_stop)
        self.stop_btn.pack(side=tk.LEFT, padx=4)
        self.stop_btn.configure(state="disabled")

        # Status
        self.status_var = tk.StringVar(value="● 已停止")
        status_lbl = ttk.Label(self, textvariable=self.status_var)
        status_lbl.grid(row=5, column=0, sticky="w", padx=4, pady=(6, 2))

        # Cycle count
        self.cycle_var = tk.StringVar(value="循环次数: 0")
        cycle_lbl = ttk.Label(self, textvariable=self.cycle_var)
        cycle_lbl.grid(row=6, column=0, sticky="w", padx=4)

        self.columnconfigure(0, weight=1)

    def _do_start(self):
        self._on_start(self.egg_var.get(), self.gulu_var.get())

    def _do_stop(self):
        self._on_stop()

    def set_running(self, running: bool):
        self._running = running
        if running:
            self.start_btn.configure(state="disabled")
            self.stop_btn.configure(state="normal")
            self.egg_combo.configure(state="disabled")
            self.gulu_combo.configure(state="disabled")
            self.status_var.set("● 运行中")
        else:
            self.start_btn.configure(state="normal")
            self.stop_btn.configure(state="disabled")
            self.egg_combo.configure(state="readonly")
            self.gulu_combo.configure(state="readonly")
            self.status_var.set("● 已停止")

    def set_cycle_count(self, n: int):
        self.cycle_var.set(f"循环次数: {n}")

    def selected_egg_name(self) -> str:
        return self.egg_var.get()

    def selected_gulu_name(self) -> str:
        return self.gulu_var.get()
