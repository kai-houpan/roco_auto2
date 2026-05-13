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
            bg="white", fg="black",
            insertbackground="black"
        )
        self.text.pack(fill=tk.BOTH, expand=True)

        self._tag_configure()

    def _tag_configure(self):
        self.text.tag_config("START", foreground="#3C5A7D")
        self.text.tag_config("OK", foreground="#2D6A2D")
        self.text.tag_config("FAIL", foreground="#B5451A")
        self.text.tag_config("ACT", foreground="#20548B")
        self.text.tag_config("SCROLL", foreground="#20548B")
        self.text.tag_config("WARN", foreground="#8B7500")
        self.text.tag_config("ERROR", foreground="#CC2200")
        self.text.tag_config("STOP", foreground="#B5451A")

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
