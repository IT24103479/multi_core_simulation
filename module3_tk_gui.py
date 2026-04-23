import io
import threading
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

import matplotlib

matplotlib.use("TkAgg")

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from dataclasses import dataclass


@dataclass(frozen=True)
class TableColumn:
    key: str
    label: str
    width: int
    anchor: str = "center"


class TableHost(ttk.Frame):
    """Simple Treeview table with scrollbar."""

    def __init__(self, master, columns: list[TableColumn], title: str):
        super().__init__(master, padding=8)
        self.columns = columns
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        ttk.Label(self, text=title, font=("Segoe UI", 11, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 6))

        self.tree = ttk.Treeview(self, columns=[c.key for c in columns], show="headings", height=12)
        self.tree.grid(row=1, column=0, sticky="nsew")

        yscroll = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        yscroll.grid(row=1, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=yscroll.set)

        for col in columns:
            self.tree.heading(col.key, text=col.label)
            self.tree.column(col.key, width=col.width, anchor=col.anchor, stretch=True)

    def clear(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

    def insert_rows(self, rows: list[dict]) -> None:
        self.clear()
        for row in rows:
            values = [row.get(c.key, "") for c in self.columns]
            self.tree.insert("", "end", values=values)


class Module3TkGUI(tk.Tk):
    """
    Module 3 GUI (Tkinter):
    - Runs Module 3 bus experiments
    - Displays the 4-subplot Matplotlib figure (no image exports)
    - Shows the printed tables/analysis in a text panel
    """

    def __init__(self) -> None:
        super().__init__()
        self.title("Module 3 – Bus & Communication (GUI)")
        self.minsize(1200, 720)

        self._worker_thread = None
        self._stop_requested = False

        self._build_style()
        self._build_layout()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_style(self) -> None:
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
        style.configure("Card.TFrame", background="#ffffff")

    def _build_layout(self) -> None:
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)

        header = ttk.Frame(root)
        header.pack(fill="x", pady=(0, 10))
        ttk.Label(header, text="Module 3 – Bus & Communication", style="Header.TLabel").pack(side="left")

        self.status_var = tk.StringVar(value="Ready.")
        ttk.Label(header, textvariable=self.status_var, style="Muted.TLabel").pack(side="right")

        controls = ttk.Frame(root)
        controls.pack(fill="x", pady=(0, 10))

        self.btn_run = ttk.Button(controls, text="Run Experiments", command=self.on_run, style="Accent.TButton")
        self.btn_run.pack(side="left", padx=(0, 8))

        self.btn_clear = ttk.Button(controls, text="Clear Output", command=self.on_clear)
        self.btn_clear.pack(side="left", padx=(0, 8))

        self.btn_stop = ttk.Button(controls, text="Stop", command=self.on_stop, state="disabled")
        self.btn_stop.pack(side="left")

        ttk.Label(
            controls,
            text="Graphs are generated from Module 3 results (no saved PNG).",
            style="Muted.TLabel",
        ).pack(side="right")

        body = ttk.Frame(root)
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=1)
        body.rowconfigure(0, weight=1)

        self.tabs = ttk.Notebook(body)
        self.tabs.grid(row=0, column=0, sticky="nsew")

        # Tab 1: Graphs
        graphs = ttk.Frame(self.tabs, padding=12)
        graphs.columnconfigure(0, weight=1)
        graphs.rowconfigure(0, weight=1)
        self.tabs.add(graphs, text="Graphs (4 plots)")

        self.fig_frame = ttk.Frame(graphs, padding=8)
        self.fig_frame.grid(row=0, column=0, sticky="nsew")
        self.fig_frame.rowconfigure(0, weight=1)
        self.fig_frame.columnconfigure(0, weight=1)

        self._canvas = None
        self._canvas_widget = None
        self._fig_placeholder = ttk.Label(
            self.fig_frame,
            text="Click “Run Experiments” to generate the 4 graphs.",
            style="Muted.TLabel",
            anchor="center",
            justify="center",
        )
        self._fig_placeholder.grid(row=0, column=0, sticky="nsew")

        # Tab 2: Metrics
        metrics = ttk.Frame(self.tabs, padding=12)
        metrics.columnconfigure(0, weight=1)
        metrics.rowconfigure(0, weight=1)
        self.tabs.add(metrics, text="Metrics Table")

        cols = [
            TableColumn("Processors", "Processors", 90),
            TableColumn("WallTimeCont", "Wall Time (Contended)", 170),
            TableColumn("WallTimeCtrl", "Wall Time (Controlled)", 170),
            TableColumn("ThroughputCont", "Throughput (Contended)", 175),
            TableColumn("ThroughputCtrl", "Throughput (Controlled)", 175),
            TableColumn("AvgWaitCont", "Avg Wait (Contended)", 155),
            TableColumn("AvgWaitCtrl", "Avg Wait (Controlled)", 155),
        ]
        self.table = TableHost(metrics, cols, title="Module 3 metrics")
        self.table.grid(row=0, column=0, sticky="nsew")

        # Tab 3: Raw output
        raw = ttk.Frame(self.tabs, padding=12)
        raw.columnconfigure(0, weight=1)
        raw.rowconfigure(1, weight=1)
        self.tabs.add(raw, text="Raw Output")

        ttk.Label(raw, text="Results (tables + analysis)", font=("Segoe UI", 11, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 6)
        )

        self.out_text = tk.Text(raw, wrap="none", height=20, background="#ffffff")
        self.out_text.grid(row=1, column=0, sticky="nsew")

        yscroll = ttk.Scrollbar(raw, orient="vertical", command=self.out_text.yview)
        yscroll.grid(row=1, column=1, sticky="ns")
        self.out_text.configure(yscrollcommand=yscroll.set)

    # ---------------------------
    # Actions
    # ---------------------------
    def on_run(self) -> None:
        if self._worker_thread and self._worker_thread.is_alive():
            return

        self._stop_requested = False
        self.btn_run.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self._set_status("Running experiments…")

        self._worker_thread = threading.Thread(target=self._run_worker, daemon=True)
        self._worker_thread.start()

    def on_stop(self) -> None:
        # Module 3 simulation itself isn't designed for mid-run cancellation;
        # this just disables re-run and updates status.
        self._stop_requested = True
        self._set_status("Stop requested (will apply after current run).")

    def on_clear(self) -> None:
        self.out_text.delete("1.0", "end")

    # ---------------------------
    # Worker
    # ---------------------------
    def _run_worker(self) -> None:
        try:
            # Import module 3 with its special folder name using importlib
            import importlib.util
            from pathlib import Path
            import sys

            module3_path = Path(__file__).parent / "MODULE_3_Bus_&_Communication" / "module3_bus_communication.py"
            spec = importlib.util.spec_from_file_location("module3_bus_communication", module3_path)
            module3 = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module3)

            # Capture printed tables/analysis into a string
            buf = io.StringIO()
            contended, controlled = None, None
            with _redirect_stdout(buf):
                contended, controlled = module3.collect_results()
                module3.print_results_table(contended, controlled)
                module3.print_analysis(contended, controlled)

            if self._stop_requested:
                self.after(0, lambda: self._finish_run(cancelled=True))
                return

            fig = module3.plot_results(contended, controlled, show=False, save_path=None)
            output = buf.getvalue()

            rows = []
            for c, k in zip(contended, controlled):
                rows.append(
                    {
                        "Processors": c["num_processors"],
                        "WallTimeCont": f'{c["wall_time"]:.4f}s',
                        "WallTimeCtrl": f'{k["wall_time"]:.4f}s',
                        "ThroughputCont": f'{c["throughput"]:.2f}',
                        "ThroughputCtrl": f'{k["throughput"]:.2f}',
                        "AvgWaitCont": f'{c["avg_wait"]:.6f}s',
                        "AvgWaitCtrl": f'{k["avg_wait"]:.6f}s',
                    }
                )

            self.after(0, lambda: self._apply_results(fig, rows, output))
        except Exception as e:
            self.after(0, lambda: self._show_error(str(e)))
        finally:
            self.after(0, lambda: self._finish_run(cancelled=False))

    def _apply_results(self, fig, rows: list[dict], output: str) -> None:
        # Text
        self.out_text.delete("1.0", "end")
        self.out_text.insert("1.0", output.strip() + "\n")

        # Table
        self.table.insert_rows(rows)

        # Figure
        if self._fig_placeholder:
            self._fig_placeholder.destroy()
            self._fig_placeholder = None

        if self._canvas_widget is not None:
            self._canvas_widget.destroy()
            self._canvas_widget = None
            self._canvas = None

        self._canvas = FigureCanvasTkAgg(fig, master=self.fig_frame)
        self._canvas_widget = self._canvas.get_tk_widget()
        self._canvas_widget.configure(background="#ffffff", highlightthickness=1)
        self._canvas_widget.grid(row=0, column=0, sticky="nsew")
        self._canvas.draw_idle()

        self._set_status("Done. Graphs updated.")

    def _finish_run(self, cancelled: bool) -> None:
        self.btn_run.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        if cancelled:
            self._set_status("Stopped.")

    # ---------------------------
    # Utilities
    # ---------------------------
    def _set_status(self, text: str) -> None:
        self.status_var.set(text)

    def _show_error(self, msg: str) -> None:
        self.btn_run.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        self._set_status("Error.")
        messagebox.showerror("Module 3 GUI error", msg)

    def _on_close(self) -> None:
        self._stop_requested = True
        self.destroy()


class _redirect_stdout:
    def __init__(self, target):
        self.target = target
        self._old = None

    def __enter__(self):
        import sys

        self._old = sys.stdout
        sys.stdout = self.target
        return self

    def __exit__(self, exc_type, exc, tb):
        import sys

        sys.stdout = self._old
        return False


def main() -> None:
    app = Module3TkGUI()
    app.mainloop()


if __name__ == "__main__":
    main()

