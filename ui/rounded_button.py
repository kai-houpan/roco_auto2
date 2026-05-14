import tkinter as tk
import tkinter.font as tkfont


class RoundedButton(tk.Canvas):
    """Canvas-based button with rounded corners and hover states."""

    RADIUS = 8
    PADX = 16
    PADY = 6

    def __init__(self, parent, text: str, command=None, accent: str = "#112DA5",
                 font=("", 9), **kw):
        tk.Canvas.__init__(self, parent, highlightthickness=0,
                           borderwidth=0, **kw)
        self._command = command
        self._accent = accent
        self._text = text
        self._font = font
        self._enabled = True
        self._hover = False

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)

        # Measure and set size after widget is realized
        self.bind("<Map>", lambda e: self._measure_and_draw())

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------
    def set_enabled(self, enabled: bool):
        self._enabled = enabled
        self._hover = False
        self._redraw()

    # ------------------------------------------------------------------
    # Sizing
    # ------------------------------------------------------------------
    def _measure_and_draw(self):
        f = tkfont.Font(font=self._font)
        tw = f.measure(self._text)
        th = f.metrics("linespace")
        w = tw + self.PADX * 2
        h = th + self.PADY * 2
        self.configure(width=w, height=h)
        self._redraw()

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------
    def _redraw(self):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 4 or h < 4:
            return
        r = self.RADIUS

        if not self._enabled:
            fill = "#E0E0E0"
            text_color = "#A0A0A0"
            outline = "#C0C0C0"
        elif self._hover:
            fill = self._accent
            text_color = "white"
            outline = self._accent
        else:
            fill = "white"
            text_color = self._accent
            outline = self._accent

        self.create_polygon(
            r, 0,  w - r, 0,  w - r, 0,  w, 0,  w, r,
            w, r,  w, h - r,  w, h - r,  w, h,  w - r, h,
            w - r, h,  r, h,  r, h,  0, h,  0, h - r,
            0, h - r,  0, r,  0, r,  0, 0,  r, 0,
            fill=fill, outline=outline, width=1, smooth=True)

        self.create_text(
            w // 2, h // 2, text=self._text, fill=text_color,
            font=self._font, anchor="center")

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------
    def _on_enter(self, event):
        if self._enabled:
            self._hover = True
            self._redraw()

    def _on_leave(self, event):
        if self._enabled:
            self._hover = False
            self._redraw()

    def _on_click(self, event):
        if self._enabled and self._command:
            self._command()
