import tkinter as tk
from tkinter import ttk, scrolledtext
from datetime import datetime
import threading


class LogPanel(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self._create_widgets()

    def _create_widgets(self):
        label = ttk.Label(self, text="运行日志")
        label.pack(anchor="w", padx=4, pady=(0, 2))

        self.text = scrolledtext.ScrolledText(
            self, wrap=tk.WORD, state="disabled",
            bg="#1E1E1E", fg="#BBBBBB",
            insertbackground="#BBBBBB",
            font=("Consolas", 10)
        )
        self.text.pack(fill=tk.BOTH, expand=True)

        self._tag_configure()

    def _tag_configure(self):
        self.text.tag_config("START", foreground="#A9B7C6")
        self.text.tag_config("OK", foreground="#6A8759")
        self.text.tag_config("FAIL", foreground="#CC7832")
        self.text.tag_config("ACT", foreground="#6897BB")
        self.text.tag_config("SCROLL", foreground="#6897BB")
        self.text.tag_config("WARN", foreground="#BBB529")
        self.text.tag_config("ERROR", foreground="#FF6B68")
        self.text.tag_config("STOP", foreground="#CC7832")

    def _write(self, level: str, message: str):
        ts = datetime.now().strftime("%H:%M:%S.%f")[:12]
        line = f"[{ts}] {level:<6} {message}\n"
        self.text.configure(state="normal")
        self.text.insert(tk.END, line, level)
        self.text.see(tk.END)
        self.text.configure(state="disabled")

    def start(self, message: str):       self._write("START", message)
    def ok(self, message: str):          self._write("OK", message)
    def fail(self, message: str):        self._write("FAIL", message)
    def act(self, message: str):         self._write("ACT", message)
    def scroll(self, message: str):      self._write("SCROLL", message)
    def warn(self, message: str):        self._write("WARN", message)
    def error(self, message: str):       self._write("ERROR", message)
    def stop(self, message: str):        self._write("STOP", message)
