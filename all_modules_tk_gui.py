import io
import threading
import tkinter as tk
from dataclasses import dataclass
from tkinter import messagebox
from tkinter import ttk

import matplotlib

matplotlib.use("TkAgg")

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


@dataclass(frozen=True)
class TableColumn:
    key: str
    label: str
    width: int
    anchor: str = "center"


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


class FigureHost(ttk.Frame):
    """Reusable frame that embeds a Matplotlib Figure."""

    def __init__(self, master):
        super().__init__(master, padding=8)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self._canvas = None
        self._canvas_widget = None
        self._placeholder = ttk.Label(self, text="Run to generate graphs.", anchor="center", justify="center")
        self._placeholder.grid(row=0, column=0, sticky="nsew")

    def set_figure(self, fig) -> None:
        if self._placeholder is not None:
            self._placeholder.destroy()
            self._placeholder = None

        if self._canvas_widget is not None:
            self._canvas_widget.destroy()
            self._canvas_widget = None
            self._canvas = None

        self._canvas = FigureCanvasTkAgg(fig, master=self)
        self._canvas_widget = self._canvas.get_tk_widget()
        self._canvas_widget.configure(background="#ffffff", highlightthickness=1)
        self._canvas_widget.grid(row=0, column=0, sticky="nsew")
        self._canvas.draw_idle()


class TableHost(ttk.Frame):
    """Reusable Treeview table with scrollbar."""

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


class Module3Panel(ttk.Frame):
    """Module 3 tab: shows the original 4-graph figure + a clear metrics table."""

    def __init__(self, master, set_status):
        super().__init__(master)
        self._set_status = set_status
        self._thread = None
        self._stop_requested = False

        self.columnconfigure(0, weight=3)
        self.columnconfigure(1, weight=2)
        self.rowconfigure(1, weight=1)

        header = ttk.Frame(self, padding=(12, 12, 12, 0))
        header.grid(row=0, column=0, columnspan=2, sticky="ew")

        ttk.Label(
            header,
            text="Module 3: Bus & Communication",
            font=("Segoe UI", 12, "bold"),
        ).pack(side="left")

        btns = ttk.Frame(header)
        btns.pack(side="right")
        self.btn_run = ttk.Button(btns, text="Run Module 3", command=self.on_run)
        self.btn_run.pack(side="left", padx=(0, 8))
        self.btn_stop = ttk.Button(btns, text="Stop", command=self.on_stop, state="disabled")
        self.btn_stop.pack(side="left")

        self.fig_host = FigureHost(self)
        self.fig_host.grid(row=1, column=0, sticky="nsew", padx=(12, 6), pady=12)

        cols = [
            TableColumn("Processors", "Processors", 90),
            TableColumn("WallTimeCont", "Wall Time (Contended)", 160),
            TableColumn("WallTimeCtrl", "Wall Time (Controlled)", 160),
            TableColumn("ThroughputCont", "Throughput (Contended)", 170),
            TableColumn("ThroughputCtrl", "Throughput (Controlled)", 170),
            TableColumn("AvgWaitCont", "Avg Wait (Contended)", 150),
            TableColumn("AvgWaitCtrl", "Avg Wait (Controlled)", 150),
        ]
        self.table_host = TableHost(self, cols, title="Module 3 metrics (clear table)")
        self.table_host.grid(row=1, column=1, sticky="nsew", padx=(6, 12), pady=12)

        self.out_text = tk.Text(self, wrap="none", height=10, background="#ffffff")
        self.out_text.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=12, pady=(0, 12))

    def on_run(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_requested = False
        self.btn_run.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self._set_status("Module 3 running…")
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def on_stop(self) -> None:
        self._stop_requested = True
        self._set_status("Module 3 stop requested (applies after run).")

    def _worker(self) -> None:
        try:
            import importlib.util
            from pathlib import Path

            module3_path = (
                Path(__file__).parent / "MODULE_3_Bus_&_Communication" / "module3_bus_communication.py"
            )
            spec = importlib.util.spec_from_file_location("module3_bus_communication", module3_path)
            module3 = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module3)

            buf = io.StringIO()
            with _redirect_stdout(buf):
                contended, controlled = module3.collect_results()
                module3.print_results_table(contended, controlled)
                module3.print_analysis(contended, controlled)

            if self._stop_requested:
                self.after(0, self._finish_cancelled)
                return

            fig = module3.plot_results(contended, controlled, show=False, save_path=None)
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

            out = buf.getvalue().strip()
            self.after(0, lambda: self._apply(fig, rows, out))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Module 3 error", str(e)))
        finally:
            self.after(0, self._finish)

    def _apply(self, fig, rows, out: str) -> None:
        self.fig_host.set_figure(fig)
        self.table_host.insert_rows(rows)
        self.out_text.delete("1.0", "end")
        self.out_text.insert("1.0", out + "\n")
        self._set_status("Module 3 done (graphs + table updated).")

    def _finish_cancelled(self) -> None:
        self._set_status("Module 3 stopped.")

    def _finish(self) -> None:
        self.btn_run.configure(state="normal")
        self.btn_stop.configure(state="disabled")


class Module1Panel(ttk.Frame):
    def __init__(self, master, set_status):
        super().__init__(master)
        self._set_status = set_status
        self._thread = None

        self.columnconfigure(0, weight=3)
        self.columnconfigure(1, weight=2)
        self.rowconfigure(1, weight=1)

        header = ttk.Frame(self, padding=(12, 12, 12, 0))
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        ttk.Label(header, text="Module 1: Parallelism", font=("Segoe UI", 12, "bold")).pack(side="left")
        self.btn_run = ttk.Button(header, text="Run Module 1", command=self.on_run)
        self.btn_run.pack(side="right")

        self.fig_host = FigureHost(self)
        self.fig_host.grid(row=1, column=0, sticky="nsew", padx=(12, 6), pady=12)

        cols = [
            TableColumn("Method", "Method", 130, anchor="w"),
            TableColumn("Workers", "Workers", 80),
            TableColumn("Time", "Time (s)", 100),
            TableColumn("Speedup", "Speedup", 90),
            TableColumn("Efficiency", "Efficiency", 110),
        ]
        self.table_host = TableHost(self, cols, title="Module 1 results")
        self.table_host.grid(row=1, column=1, sticky="nsew", padx=(6, 12), pady=12)

    def on_run(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self.btn_run.configure(state="disabled")
        self._set_status("Module 1 running…")
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def _worker(self) -> None:
        try:
            from MODULE_1_Parallelism.module1_parallelism import (
                N,
                measure_time,
                multiprocessing_execution,
                sequential_execution,
                threaded_execution,
            )
            from matplotlib.figure import Figure
            import numpy as np

            seq_time, _ = measure_time(sequential_execution, N)

            records = []
            for threads in (2, 4, 8):
                t_time, _ = measure_time(threaded_execution, N, threads)
                speedup = seq_time / t_time if t_time else 0.0
                efficiency = speedup / threads if threads else 0.0
                records.append(
                    {
                        "Method": "Threading",
                        "Workers": threads,
                        "Time": t_time,
                        "Speedup": speedup,
                        "Efficiency": efficiency,
                    }
                )

            for procs in (2, 4, 8):
                p_time, _ = measure_time(multiprocessing_execution, N, procs)
                speedup = seq_time / p_time if p_time else 0.0
                efficiency = speedup / procs if procs else 0.0
                records.append(
                    {
                        "Method": "Multiprocessing",
                        "Workers": procs,
                        "Time": p_time,
                        "Speedup": speedup,
                        "Efficiency": efficiency,
                    }
                )

            # Plot: time + speedup + efficiency (3 stacked)
            fig = Figure(figsize=(10, 7), dpi=100)
            ax1 = fig.add_subplot(3, 1, 1)
            ax2 = fig.add_subplot(3, 1, 2)
            ax3 = fig.add_subplot(3, 1, 3)

            def _series(method: str, key: str):
                rows = [r for r in records if r["Method"] == method]
                rows = sorted(rows, key=lambda r: r["Workers"])
                x = [r["Workers"] for r in rows]
                y = [r[key] for r in rows]
                return x, y

            for method, color in (("Threading", "#1f77b4"), ("Multiprocessing", "#d62728")):
                x, y = _series(method, "Time")
                ax1.plot(x, y, marker="o", linewidth=2, label=method, color=color)
            ax1.set_title("Execution Time vs Workers", fontweight="bold")
            ax1.set_xlabel("Workers")
            ax1.set_ylabel("Time (s)")
            ax1.grid(True, linestyle="--", alpha=0.35)
            ax1.legend()

            for method, color in (("Threading", "#1f77b4"), ("Multiprocessing", "#d62728")):
                x, y = _series(method, "Speedup")
                ax2.bar([str(v) + ("\nT" if method == "Threading" else "\nP") for v in x], y, alpha=0.75, color=color)
            ax2.set_title("Speedup (baseline = sequential)", fontweight="bold")
            ax2.set_ylabel("Speedup")
            ax2.grid(True, axis="y", linestyle="--", alpha=0.35)

            for method, color in (("Threading", "#1f77b4"), ("Multiprocessing", "#d62728")):
                x, y = _series(method, "Efficiency")
                ax3.plot(x, y, marker="o", linewidth=2, label=method, color=color)
            ax3.set_title("Efficiency vs Workers", fontweight="bold")
            ax3.set_xlabel("Workers")
            ax3.set_ylabel("Efficiency")
            ax3.set_ylim(0, 1.05)
            ax3.grid(True, linestyle="--", alpha=0.35)
            ax3.legend()

            fig.tight_layout(pad=2.0)

            table_rows = [
                {
                    "Method": r["Method"],
                    "Workers": r["Workers"],
                    "Time": f'{r["Time"]:.4f}',
                    "Speedup": f'{r["Speedup"]:.2f}',
                    "Efficiency": f'{r["Efficiency"]:.2%}',
                }
                for r in sorted(records, key=lambda r: (r["Method"], r["Workers"]))
            ]

            self.after(0, lambda: self._apply(fig, table_rows))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Module 1 error", str(e)))
        finally:
            self.after(0, self._finish)

    def _apply(self, fig, rows):
        self.fig_host.set_figure(fig)
        self.table_host.insert_rows(rows)
        self._set_status("Module 1 done.")

    def _finish(self):
        self.btn_run.configure(state="normal")


class Module4Panel(ttk.Frame):
    def __init__(self, master, set_status):
        super().__init__(master)
        self._set_status = set_status
        self._thread = None

        self.columnconfigure(0, weight=3)
        self.columnconfigure(1, weight=2)
        self.rowconfigure(1, weight=1)

        header = ttk.Frame(self, padding=(12, 12, 12, 0))
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        ttk.Label(header, text="Module 4: Cache Coherence", font=("Segoe UI", 12, "bold")).pack(side="left")
        self.btn_run = ttk.Button(header, text="Run Module 4", command=self.on_run)
        self.btn_run.pack(side="right")

        self.fig_host = FigureHost(self)
        self.fig_host.grid(row=1, column=0, sticky="nsew", padx=(12, 6), pady=12)

        cols = [
            TableColumn("Scenario", "Scenario", 150, anchor="w"),
            TableColumn("Time", "Time (s)", 110),
            TableColumn("Speedup", "Speedup", 100),
            TableColumn("Relative", "Relative", 100),
        ]
        self.table_host = TableHost(self, cols, title="Module 4 results")
        self.table_host.grid(row=1, column=1, sticky="nsew", padx=(6, 12), pady=12)

    def on_run(self):
        if self._thread and self._thread.is_alive():
            return
        self.btn_run.configure(state="disabled")
        self._set_status("Module 4 running…")
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def _worker(self):
        try:
            from MODULE_4_Cache_Coherence.FuLLCode import plot_execution_times, plot_speedup, run_tests
            from matplotlib.figure import Figure

            results = run_tests()
            baseline = results["Baseline"]
            rows = []
            for name, t in results.items():
                rows.append(
                    {
                        "Scenario": name,
                        "Time": f"{t:.4f}",
                        "Speedup": f"{baseline / t:.2f}",
                        "Relative": f"{t / baseline:.2f}",
                    }
                )

            # Combine two Module4 figures into one (2x1) for clarity
            fig_time = plot_execution_times(results)
            fig_speedup = plot_speedup(results)

            combo = Figure(figsize=(10, 7), dpi=100)
            ax1 = combo.add_subplot(2, 1, 1)
            ax2 = combo.add_subplot(2, 1, 2)

            # Copy artists (simple re-plot for reliability)
            labels = list(results.keys())
            values = list(results.values())
            ax1.bar(labels, values, color="steelblue", edgecolor="black")
            ax1.set_title("Execution Time Comparison", fontweight="bold")
            ax1.set_ylabel("Time (s)")
            ax1.tick_params(axis="x", rotation=15)
            ax1.grid(True, axis="y", linestyle="--", alpha=0.35)

            speed = [baseline / v for v in values]
            ax2.bar(labels, speed, color="coral", edgecolor="black")
            ax2.set_title("Speedup vs Baseline", fontweight="bold")
            ax2.set_ylabel("Speedup")
            ax2.tick_params(axis="x", rotation=15)
            ax2.grid(True, axis="y", linestyle="--", alpha=0.35)

            combo.tight_layout(pad=2.0)

            self.after(0, lambda: self._apply(combo, rows))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Module 4 error", str(e)))
        finally:
            self.after(0, self._finish)

    def _apply(self, fig, rows):
        self.fig_host.set_figure(fig)
        self.table_host.insert_rows(rows)
        self._set_status("Module 4 done.")

    def _finish(self):
        self.btn_run.configure(state="normal")


class AllModulesDashboard(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Multi-Core Simulation – All Modules (Tkinter GUI)")
        self.minsize(1280, 760)

        self._build_style()

        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)
        root.rowconfigure(1, weight=1)
        root.columnconfigure(0, weight=1)

        header = ttk.Frame(root)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ttk.Label(header, text="Multi-Core Simulation Dashboard", font=("Segoe UI", 14, "bold")).pack(side="left")
        self.status_var = tk.StringVar(value="Ready.")
        ttk.Label(header, textvariable=self.status_var, foreground="#586174").pack(side="right")

        self.notebook = ttk.Notebook(root)
        self.notebook.grid(row=1, column=0, sticky="nsew")

        self.module1 = Module1Panel(self.notebook, self._set_status)
        self.module3 = Module3Panel(self.notebook, self._set_status)
        self.module4 = Module4Panel(self.notebook, self._set_status)

        self.notebook.add(self.module1, text="Module 1")
        self.notebook.add(self.module3, text="Module 3 (correct graphs)")
        self.notebook.add(self.module4, text="Module 4")

        footer = ttk.Frame(root)
        footer.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        ttk.Label(
            footer,
            text="Tip: Module 3 tab uses your original `plot_results()` (4 graphs) for accurate display.",
            foreground="#586174",
        ).pack(side="left")

    def _build_style(self) -> None:
        style = ttk.Style(self)
        if "vista" in style.theme_names():
            style.theme_use("vista")
        elif "clam" in style.theme_names():
            style.theme_use("clam")

        style.configure("TFrame", background="#f6f7fb")
        style.configure("TLabel", background="#f6f7fb")

    def _set_status(self, text: str) -> None:
        self.status_var.set(text)


def main() -> None:
    app = AllModulesDashboard()
    app.mainloop()


if __name__ == "__main__":
    main()

