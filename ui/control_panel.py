import tkinter as tk
from tkinter import ttk


class ControlPanel(ttk.Frame):
    def __init__(self, parent, egg_names: list[str], gulu_names: list[str],
                 config_names: list[str], on_start, on_stop, on_test, on_config_change):
        super().__init__(parent)
        self.egg_names = egg_names
        self.gulu_names = gulu_names
        self.config_names = config_names
        self._on_start = on_start
        self._on_stop = on_stop
        self._on_test = on_test
        self._on_config_change = on_config_change
        self._running = False
        self.ACCENT = "#112DA5"
        self._create_widgets()

    def _create_widgets(self):
        # ---- Screen config ----
        ttk.Label(self, text="屏幕设置:").grid(
            row=0, column=0, sticky="w", padx=4, pady=(6, 2))
        self.config_var = tk.StringVar(value=self.config_names[0] if self.config_names else "")
        self.config_combo = ttk.Combobox(
            self, textvariable=self.config_var, values=self.config_names, state="readonly")
        self.config_combo.grid(row=1, column=0, sticky="ew", padx=4, pady=(0, 4))
        self.config_combo.bind("<<ComboboxSelected>>", self._on_config_selected)

        # ---- Egg selection ----
        ttk.Label(self, text="选择目标蛋:").grid(
            row=2, column=0, sticky="w", padx=4, pady=(6, 2))

        egg_frame = ttk.Frame(self)
        egg_frame.grid(row=3, column=0, sticky="ew", padx=4, pady=(0, 4))
        egg_frame.columnconfigure(0, weight=1)

        self.egg_var = tk.StringVar(value=self.egg_names[0] if self.egg_names else "")
        self.egg_combo = ttk.Combobox(
            egg_frame, textvariable=self.egg_var, values=self.egg_names, state="readonly")
        self.egg_combo.grid(row=0, column=0, sticky="ew")

        self.add_btn = ttk.Button(egg_frame, text="＋ 加入队列",
                                  command=self._on_add_to_queue)
        self.add_btn.grid(row=0, column=1, padx=(4, 0))

        # ---- Queue ----
        ttk.Label(self, text="任务队列:").grid(
            row=4, column=0, sticky="w", padx=4, pady=(4, 2))

        self.queue_listbox = tk.Listbox(
            self, height=3, bg="white", fg="black",
            selectbackground=self.ACCENT, selectforeground="white",
            activestyle="none", exportselection=False)
        self.queue_listbox.grid(row=5, column=0, sticky="ew", padx=4, pady=(0, 2))

        queue_btn_frame = ttk.Frame(self)
        queue_btn_frame.grid(row=6, column=0, sticky="w", padx=4, pady=(0, 4))

        self.remove_btn = ttk.Button(queue_btn_frame, text="移除",
                                     command=self._on_remove_from_queue)
        self.remove_btn.pack(side=tk.LEFT, padx=(0, 4))

        self.up_btn = ttk.Button(queue_btn_frame, text="▲ 上移",
                                 command=self._on_move_up)
        self.up_btn.pack(side=tk.LEFT, padx=(0, 4))

        self.down_btn = ttk.Button(queue_btn_frame, text="▼ 下移",
                                   command=self._on_move_down)
        self.down_btn.pack(side=tk.LEFT)

        # ---- Gulu selection ----
        ttk.Label(self, text="选择咕噜球:").grid(
            row=7, column=0, sticky="w", padx=4, pady=(6, 2))
        self.gulu_var = tk.StringVar(value=self.gulu_names[0] if self.gulu_names else "")
        self.gulu_combo = ttk.Combobox(
            self, textvariable=self.gulu_var, values=self.gulu_names, state="readonly")
        self.gulu_combo.grid(row=8, column=0, sticky="ew", padx=4, pady=(0, 4))

        # ---- Buttons ----
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=9, column=0, pady=(8, 4))

        self.start_btn = ttk.Button(btn_frame, text="▶ 启动", command=self._do_start)
        self.start_btn.pack(side=tk.LEFT, padx=4)

        self.stop_btn = ttk.Button(btn_frame, text="⏹ 停止", command=self._do_stop)
        self.stop_btn.pack(side=tk.LEFT, padx=4)
        self.stop_btn.configure(state="disabled")

        self.test_btn = ttk.Button(btn_frame, text="🔍 测试匹配", command=self._on_test)
        self.test_btn.pack(side=tk.LEFT, padx=4)

        # ---- Status ----
        self.status_var = tk.StringVar(value="● 已停止")
        ttk.Label(self, textvariable=self.status_var).grid(
            row=10, column=0, sticky="w", padx=4, pady=(6, 2))

        # ---- Cycle count ----
        self.cycle_var = tk.StringVar(value="循环次数: 0")
        ttk.Label(self, textvariable=self.cycle_var).grid(
            row=11, column=0, sticky="w", padx=4)

        # ---- Post-workflow options ----
        self.auto_close_var = tk.BooleanVar(value=False)
        self.auto_close_cb = ttk.Checkbutton(
            self, text="工作流结束后自动关闭游戏窗口", variable=self.auto_close_var)
        self.auto_close_cb.grid(row=12, column=0, sticky="w", padx=4, pady=(8, 2))

        self.auto_shutdown_var = tk.BooleanVar(value=False)
        self.auto_shutdown_cb = ttk.Checkbutton(
            self, text="工作流结束后自动关机", variable=self.auto_shutdown_var)
        self.auto_shutdown_cb.grid(row=13, column=0, sticky="w", padx=4, pady=(0, 2))

        self.columnconfigure(0, weight=1)

    # ------------------------------------------------------------------
    # Config
    # ------------------------------------------------------------------
    def _on_config_selected(self, event):
        self._on_config_change(self.config_var.get())

    def selected_config_name(self) -> str:
        return self.config_var.get()

    # ------------------------------------------------------------------
    # Queue management
    # ------------------------------------------------------------------
    def _on_add_to_queue(self):
        name = self.egg_var.get()
        if not name:
            return
        self.queue_listbox.insert(tk.END, name)

    def _on_remove_from_queue(self):
        sel = self.queue_listbox.curselection()
        if sel:
            self.queue_listbox.delete(sel[0])

    def _on_move_up(self):
        sel = self.queue_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx == 0:
            return
        item = self.queue_listbox.get(idx)
        self.queue_listbox.delete(idx)
        self.queue_listbox.insert(idx - 1, item)
        self.queue_listbox.selection_set(idx - 1)

    def _on_move_down(self):
        sel = self.queue_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx >= self.queue_listbox.size() - 1:
            return
        item = self.queue_listbox.get(idx)
        self.queue_listbox.delete(idx)
        self.queue_listbox.insert(idx + 1, item)
        self.queue_listbox.selection_set(idx + 1)

    def remove_queue_item(self, index: int):
        """Remove item at index from the listbox (called when automator
        exhausts an egg)."""
        if 0 <= index < self.queue_listbox.size():
            self.queue_listbox.delete(index)

    def get_egg_queue(self) -> list[str]:
        """Return the ordered egg name list. Falls back to single dropdown
        selection if queue is empty."""
        items = self.queue_listbox.get(0, tk.END)
        if items:
            return list(items)
        return [self.egg_var.get()]

    # ------------------------------------------------------------------
    # Start / Stop
    # ------------------------------------------------------------------
    def _do_start(self):
        self._on_start(self.get_egg_queue(), self.gulu_var.get())

    def _do_stop(self):
        self._on_stop()

    def set_running(self, running: bool):
        self._running = running
        state_btn = "disabled" if running else "normal"
        state_combo = "disabled" if running else "readonly"

        self.start_btn.configure(state=state_btn)
        self.stop_btn.configure(state="normal" if running else "disabled")
        self.test_btn.configure(state=state_btn)
        self.config_combo.configure(state=state_combo)
        self.egg_combo.configure(state=state_combo)
        self.gulu_combo.configure(state=state_combo)
        self.add_btn.configure(state=state_btn)
        self.remove_btn.configure(state=state_btn)
        self.up_btn.configure(state=state_btn)
        self.down_btn.configure(state=state_btn)
        self.auto_close_cb.configure(state=state_btn)
        self.auto_shutdown_cb.configure(state=state_btn)

        self.status_var.set("● 运行中" if running else "● 已停止")

    def set_cycle_count(self, n: int):
        self.cycle_var.set(f"循环次数: {n}")

    def selected_egg_name(self) -> str:
        return self.egg_var.get()

    def selected_gulu_name(self) -> str:
        return self.gulu_var.get()

    def refresh_dictionaries(self, egg_names: list[str], gulu_names: list[str]):
        self.egg_names = egg_names
        self.gulu_names = gulu_names
        self.egg_combo["values"] = egg_names
        self.gulu_combo["values"] = gulu_names
        if egg_names:
            self.egg_var.set(egg_names[0])
        if gulu_names:
            self.gulu_var.set(gulu_names[0])
        self.queue_listbox.delete(0, tk.END)
