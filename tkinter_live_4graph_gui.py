import math
import random
import sys
import tkinter as tk
from collections import deque
from dataclasses import dataclass
from tkinter import filedialog, messagebox
from tkinter import ttk

import matplotlib

# Use TkAgg backend for embedding in Tkinter
matplotlib.use("TkAgg")

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


try:
    from PIL import Image, ImageTk
except Exception:  # Pillow is optional but recommended (jpg/png support)
    Image = None
    ImageTk = None


@dataclass(frozen=True)
class PlotConfig:
    title: str
    xlabel: str = "Time (t)"
    ylabel: str = "Value"


class LiveLinePlot:
    """One live-updating line plot backed by a deque ring buffer."""

    def __init__(self, ax, config: PlotConfig, max_points: int = 120) -> None:
        self.ax = ax
        self.config = config
        self.max_points = max_points

        self.x = deque(maxlen=max_points)
        self.y = deque(maxlen=max_points)
        self.t = 0

        (self.line,) = self.ax.plot([], [], linewidth=2.0)
        self._setup_axes()

    def _setup_axes(self) -> None:
        self.ax.set_title(self.config.title, fontsize=11, fontweight="bold")
        self.ax.set_xlabel(self.config.xlabel, fontsize=9)
        self.ax.set_ylabel(self.config.ylabel, fontsize=9)
        self.ax.grid(True, linestyle="--", alpha=0.35)

    def reset(self) -> None:
        self.x.clear()
        self.y.clear()
        self.t = 0
        self.line.set_data([], [])
        self.ax.relim()
        self.ax.autoscale_view()

    def step(self) -> None:
        """Append one new sample (synthetic streaming data)."""
        self.t += 1

        # Mix of sine + random walk noise so each chart behaves differently.
        base = math.sin(self.t / 10.0) * 10.0
        drift = (self.y[-1] if self.y else 0.0) * 0.02
        noise = random.uniform(-2.0, 2.0)
        value = base + drift + noise

        self.x.append(self.t)
        self.y.append(value)

        self.line.set_data(list(self.x), list(self.y))

        # Keep view stable and readable
        self.ax.set_xlim(max(0, self.t - self.max_points), self.t + 1)
        y_min = min(self.y) if self.y else -1
        y_max = max(self.y) if self.y else 1
        pad = max(1.0, (y_max - y_min) * 0.15)
        self.ax.set_ylim(y_min - pad, y_max + pad)


class FourGraphRecreatorGUI(tk.Tk):
    """Tkinter + Matplotlib GUI: left image, right 4 live graphs."""

    def __init__(self) -> None:
        super().__init__()
        self.title("4-Graph Recreator (Tkinter + Matplotlib)")
        self.minsize(1100, 680)

        self._running = False
        self._job_id = None

        self._uploaded_pil = None
        self._uploaded_tk = None

        self._build_style()
        self._build_layout()
        self._build_plots()
        self._set_status("Ready. Upload an image, then start live graphs.")

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ----------------------------
    # UI construction
    # ----------------------------
    def _build_style(self) -> None:
        try:
            style = ttk.Style(self)
            if "vista" in style.theme_names():
                style.theme_use("vista")
            elif "clam" in style.theme_names():
                style.theme_use("clam")

            style.configure("TFrame", background="#f6f7fb")
            style.configure("TLabel", background="#f6f7fb")
            style.configure("Header.TLabel", font=("Segoe UI", 13, "bold"))
            style.configure("Muted.TLabel", foreground="#586174")
            style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"))
        except Exception:
            pass

    def _build_layout(self) -> None:
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)

        header = ttk.Frame(root)
        header.pack(fill="x", pady=(0, 10))
        ttk.Label(header, text="4-Graph GUI (Image + Live Recreated Charts)", style="Header.TLabel").pack(
            side="left"
        )

        self.status_var = tk.StringVar(value="")
        ttk.Label(header, textvariable=self.status_var, style="Muted.TLabel").pack(side="right")

        body = ttk.Frame(root)
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)

        # Left: image panel
        self.left_panel = ttk.Frame(body, padding=(8, 8))
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.left_panel.columnconfigure(0, weight=1)
        self.left_panel.rowconfigure(1, weight=1)

        ttk.Label(self.left_panel, text="Uploaded Image (4 graphs)", font=("Segoe UI", 11, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 6)
        )

        self.image_canvas = tk.Canvas(self.left_panel, background="#ffffff", highlightthickness=1)
        self.image_canvas.grid(row=1, column=0, sticky="nsew")

        self.image_hint = ttk.Label(
            self.left_panel,
            text="Tip: Upload a screenshot or image containing 4 graphs.\n"
            "Optional: We’ll show a simple 2×2 region overlay.",
            style="Muted.TLabel",
            justify="left",
        )
        self.image_hint.grid(row=2, column=0, sticky="w", pady=(8, 0))

        # Right: plots + controls
        self.right_panel = ttk.Frame(body, padding=(8, 8))
        self.right_panel.grid(row=0, column=1, sticky="nsew")
        self.right_panel.columnconfigure(0, weight=1)
        self.right_panel.rowconfigure(1, weight=1)

        controls = ttk.Frame(self.right_panel)
        controls.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        controls.columnconfigure(3, weight=1)

        self.btn_upload = ttk.Button(controls, text="Upload Image", command=self.on_upload_image, style="Accent.TButton")
        self.btn_upload.grid(row=0, column=0, padx=(0, 8))

        self.btn_start = ttk.Button(controls, text="Start Live Graph", command=self.on_start)
        self.btn_start.grid(row=0, column=1, padx=(0, 8))

        self.btn_stop = ttk.Button(controls, text="Stop", command=self.on_stop, state="disabled")
        self.btn_stop.grid(row=0, column=2)

        ttk.Label(
            controls,
            text="Updates every 1 second • Synthetic streaming data",
            style="Muted.TLabel",
        ).grid(row=0, column=4, sticky="e")

        self.plot_container = ttk.Frame(self.right_panel)
        self.plot_container.grid(row=1, column=0, sticky="nsew")
        self.plot_container.columnconfigure(0, weight=1)
        self.plot_container.rowconfigure(0, weight=1)

    def _build_plots(self) -> None:
        self.figure = Figure(figsize=(8.6, 6.2), dpi=100)
        self.figure.patch.set_facecolor("#ffffff")

        axs = self.figure.subplots(2, 2)
        self.axes = [axs[0, 0], axs[0, 1], axs[1, 0], axs[1, 1]]

        configs = [
            PlotConfig("Graph 1", xlabel="X", ylabel="Y"),
            PlotConfig("Graph 2", xlabel="X", ylabel="Y"),
            PlotConfig("Graph 3", xlabel="X", ylabel="Y"),
            PlotConfig("Graph 4", xlabel="X", ylabel="Y"),
        ]

        # Make each graph distinct by seeding slight style differences
        colors = ["#1f77b4", "#d62728", "#2ca02c", "#9467bd"]

        self.plots = []
        for ax, cfg, color in zip(self.axes, configs, colors):
            plot = LiveLinePlot(ax, cfg)
            plot.line.set_color(color)
            self.plots.append(plot)

        self.figure.tight_layout(pad=2.2)

        self.canvas = FigureCanvasTkAgg(self.figure, master=self.plot_container)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.configure(background="#ffffff", highlightthickness=1)
        self.canvas_widget.pack(fill="both", expand=True)
        self.canvas.draw_idle()

    # ----------------------------
    # Actions
    # ----------------------------
    def on_upload_image(self) -> None:
        filetypes = [
            ("Image files", "*.png *.jpg *.jpeg *.bmp *.gif"),
            ("PNG", "*.png"),
            ("JPEG", "*.jpg *.jpeg"),
            ("All files", "*.*"),
        ]
        path = filedialog.askopenfilename(title="Select an image with 4 graphs", filetypes=filetypes)
        if not path:
            return

        if Image is None or ImageTk is None:
            messagebox.showerror(
                "Missing dependency (Pillow)",
                "This app needs Pillow to display common image formats (JPG/PNG).\n\n"
                "Install it with:\n"
                "  pip install pillow",
            )
            return

        try:
            pil = Image.open(path).convert("RGB")
        except Exception as e:
            messagebox.showerror("Image load failed", f"Could not open image:\n{e}")
            return

        self._uploaded_pil = pil
        self._render_uploaded_image()
        self._set_status("Image loaded. You can start live graphs.")

    def on_start(self) -> None:
        if self._running:
            return

        # Reset plots on every new start for a clean run
        for p in self.plots:
            p.reset()

        self._running = True
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self._set_status("Live graphs running (updates every 1 second).")
        self._tick()

    def on_stop(self) -> None:
        if not self._running:
            return

        self._running = False
        if self._job_id is not None:
            try:
                self.after_cancel(self._job_id)
            except Exception:
                pass
            self._job_id = None

        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        self._set_status("Stopped.")

    # ----------------------------
    # Live update loop
    # ----------------------------
    def _tick(self) -> None:
        if not self._running:
            return

        # Update each plot with one new point
        for plot in self.plots:
            plot.step()

        self.canvas.draw_idle()
        self._job_id = self.after(1000, self._tick)

    # ----------------------------
    # Image rendering + optional region overlay
    # ----------------------------
    def _render_uploaded_image(self) -> None:
        if self._uploaded_pil is None:
            return

        # Fit image to canvas size (or a default) with aspect ratio.
        self.update_idletasks()
        cw = max(10, self.image_canvas.winfo_width())
        ch = max(10, self.image_canvas.winfo_height())

        # On first render, canvas may be small; pick a reasonable preview size.
        if cw <= 20 or ch <= 20:
            cw, ch = 480, 520
            self.image_canvas.configure(width=cw, height=ch)

        pil = self._uploaded_pil.copy()
        pil.thumbnail((cw - 10, ch - 10))
        self._uploaded_tk = ImageTk.PhotoImage(pil)

        self.image_canvas.delete("all")
        self.image_canvas.create_image(cw // 2, ch // 2, image=self._uploaded_tk, anchor="center")

        # Optional advanced placeholder: show a simple 2×2 overlay to indicate
        # "detected regions" (quadrants).
        x0 = (cw - pil.size[0]) // 2
        y0 = (ch - pil.size[1]) // 2
        x1 = x0 + pil.size[0]
        y1 = y0 + pil.size[1]

        # Quadrant lines
        midx = (x0 + x1) / 2
        midy = (y0 + y1) / 2
        self.image_canvas.create_line(midx, y0, midx, y1, fill="#00a2ff", width=2)
        self.image_canvas.create_line(x0, midy, x1, midy, fill="#00a2ff", width=2)

        # Labels
        self.image_canvas.create_text(x0 + 8, y0 + 8, text="(Q1)", anchor="nw", fill="#006aa8")
        self.image_canvas.create_text(midx + 8, y0 + 8, text="(Q2)", anchor="nw", fill="#006aa8")
        self.image_canvas.create_text(x0 + 8, midy + 8, text="(Q3)", anchor="nw", fill="#006aa8")
        self.image_canvas.create_text(midx + 8, midy + 8, text="(Q4)", anchor="nw", fill="#006aa8")

    # ----------------------------
    # Utilities
    # ----------------------------
    def _set_status(self, text: str) -> None:
        self.status_var.set(text)

    def _on_close(self) -> None:
        self.on_stop()
        self.destroy()


def main() -> None:
    # Basic dependency sanity check for a good first-run experience.
    missing = []
    if Image is None or ImageTk is None:
        missing.append("pillow")
    if missing:
        # App still runs, but image upload may not work; warn once.
        sys.stderr.write(
            "Note: optional dependency missing: "
            + ", ".join(missing)
            + ". Install with: pip install "
            + " ".join(missing)
            + "\n"
        )

    app = FourGraphRecreatorGUI()
    app.mainloop()


if __name__ == "__main__":
    main()

