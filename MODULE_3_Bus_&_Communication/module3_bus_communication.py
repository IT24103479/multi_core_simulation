"""
===============================================================
Module 3: Bus & Communication Simulation
IE2064 - Advanced Computer Organization & Architecture
Assignment 
===============================================================
"""

import threading
import time
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np

# ===============================================================
# CONFIGURATION
# ===============================================================

PROCESSOR_COUNTS   = [1, 2, 4, 8]
TRANSFERS_PER_PROC = 20
TRANSFER_TIME      = 0.02
REPEAT_RUNS        = 3
CONTENTION_PENALTY = 0.015
ARBITRATION_DELAY  = 0.0005
PERCENT            = 100

# Plot colours — defined at module level
COLOR_CONTENDED  = "#d62728"
COLOR_CONTROLLED = "#1f77b4"
COLOR_IDEAL      = "#2ca02c"


# ===============================================================
# CLASS 1: CONTENDED SHARED BUS (NO CONTROL)
# ===============================================================

class SharedBus:
    """
    Uncontrolled shared bus.
    Processors compete freely — contention penalty grows with waiter count.
    """

    def __init__(self, transfer_time: float = 0.02,
                 contention_penalty: float = 0.015) -> None:
        self.lock              = threading.Lock()
        self.transfer_time     = transfer_time
        self.contention_penalty = contention_penalty
        self.waiting_processors = 0
        self.wait_times        = []
        self._stats_lock       = threading.Lock()

    def request_and_transfer(self, processor_id: int,
                              transfers: int) -> float:
        total_start = time.perf_counter()

        for _ in range(transfers):
            wait_start = time.perf_counter()

            # Announce intention to request the bus
            with self._stats_lock:
                self.waiting_processors += 1

            # Block until bus is free
            with self.lock:
                wait_end = time.perf_counter()

                # Snapshot and record INSIDE bus lock — accurate count
                with self._stats_lock:
                    current_waiters = self.waiting_processors
                    self.wait_times.append(wait_end - wait_start)
                    # Decrement here: processor is no longer waiting,
                    # it now owns the bus
                    self.waiting_processors -= 1

                # Actual data transfer
                time.sleep(self.transfer_time)

                # Contention penalty for uncontrolled collision
                if current_waiters > 1:
                    extra_delay = (self.contention_penalty
                                   * (current_waiters - 1))
                    time.sleep(extra_delay)

        return time.perf_counter() - total_start


# ===============================================================
# CLASS 2: CONTROLLED BUS (ORDERED ARBITRATION)
# ===============================================================

class ControlledBus:
    """
    Controlled shared bus with condition-variable arbitration.
    One processor granted bus at a time — orderly queue.
    """

    def __init__(self, transfer_time: float = 0.02,
                 arbitration_delay: float = 0.0005) -> None:
        self.transfer_time    = transfer_time
        self.arbitration_delay = arbitration_delay
        self.condition        = threading.Condition()
        self.bus_busy         = False
        self.wait_times       = []
        self._stats_lock      = threading.Lock()

    def request_and_transfer(self, processor_id: int,
                              transfers: int) -> float:
        total_start = time.perf_counter()

        for _ in range(transfers):
            wait_start = time.perf_counter()

            # Request bus from arbiter — suspend if busy
            with self.condition:
                while self.bus_busy:
                    self.condition.wait()
                self.bus_busy = True

            wait_end = time.perf_counter()

            with self._stats_lock:
                self.wait_times.append(wait_end - wait_start)

            # Transfer with deadlock-safe release
            try:
                time.sleep(self.arbitration_delay)
                time.sleep(self.transfer_time)
            finally:
                with self.condition:
                    self.bus_busy = False
                    self.condition.notify()

        return time.perf_counter() - total_start


# ===============================================================
# EXPERIMENT RUNNER
# ===============================================================

def _worker(bus: object, pid: int,
            results: list, transfers: int) -> None:
    """Thread worker — defined once outside the loop."""
    results[pid] = bus.request_and_transfer(pid, transfers)


def run_experiment(bus_class: type,
                   bus_kwargs: dict,
                   num_processors: int,
                   transfers_per_proc: int,
                   repeat: int = 3) -> dict:
    """Run bus simulation `repeat` times and return averaged metrics."""

    wall_times      = []
    avg_wait_list   = []
    throughput_list = []
    util_list       = []

    for _ in range(repeat):
        bus     = bus_class(**bus_kwargs)
        results = [0.0] * num_processors
        threads = []

        wall_start = time.perf_counter()

        for i in range(num_processors):
            t = threading.Thread(
                target=_worker,
                args=(bus, i, results, transfers_per_proc)
            )
            threads.append(t)
            t.start()

        for t in threads:
            t.join(timeout=120.0)

        wall_end  = time.perf_counter()
        wall_time = wall_end - wall_start

        # Check for hung threads
        for i, t in enumerate(threads):
            if t.is_alive():
                print(f"WARNING: Thread {i} did not finish")

        total_ops  = num_processors * transfers_per_proc
        throughput = total_ops / wall_time
        util       = (total_ops * TRANSFER_TIME) / wall_time

        wall_times.append(wall_time)
        throughput_list.append(throughput)
        util_list.append(util)

        if bus.wait_times:
            avg_wait_list.append(float(np.mean(bus.wait_times)))
        else:
            avg_wait_list.append(0.0)

    return {
        "wall_time":     float(np.mean(wall_times)),
        "wall_time_std": float(np.std(wall_times)),
        "throughput":    float(np.mean(throughput_list)),
        "bus_util":      float(np.mean(util_list)),
        "avg_wait":      float(np.mean(avg_wait_list)),
        "num_processors": num_processors,
    }


# ===============================================================
# COLLECT ALL RESULTS
# ===============================================================

def collect_results() -> tuple:
    contended_results = []
    controlled_results = []

    contended_kwargs = {
        "transfer_time":     TRANSFER_TIME,
        "contention_penalty": CONTENTION_PENALTY,
    }
    controlled_kwargs = {
        "transfer_time":    TRANSFER_TIME,
        "arbitration_delay": ARBITRATION_DELAY,
    }

    print("\nRunning experiments...\n")

    for n in PROCESSOR_COUNTS:
        print(f"  Testing {n} processor(s)...", end=" ", flush=True)

        contended_results.append(
            run_experiment(SharedBus, contended_kwargs,
                           n, TRANSFERS_PER_PROC, REPEAT_RUNS)
        )
        controlled_results.append(
            run_experiment(ControlledBus, controlled_kwargs,
                           n, TRANSFERS_PER_PROC, REPEAT_RUNS)
        )
        print("Done")

    return contended_results, controlled_results


# ===============================================================
# PRINT RESULTS TABLES
# ===============================================================

def print_results_table(contended_results: list,
                        controlled_results: list) -> None:

    print("\n" + "=" * 82)
    print("  MODULE 3 - Bus & Communication Simulation Results")
    print("=" * 82)

    print("\n  TABLE 1: Total Wall-Clock Time (seconds)")
    print("  " + "-" * 74)
    print(f"  {'Processors':<12} {'Contended':<18} {'Controlled':<18} "
          f"{'Overhead %':<14} {'Reduction %'}")
    print("  " + "-" * 74)

    for c, k in zip(contended_results, controlled_results):
        n        = c["num_processors"]
        overhead  = ((c["wall_time"] - k["wall_time"])
                     / k["wall_time"]) * PERCENT
        reduction = ((c["wall_time"] - k["wall_time"])
                     / c["wall_time"]) * PERCENT
        print(f"  {n:<12} {c['wall_time']:<18.4f} {k['wall_time']:<18.4f} "
              f"{overhead:<14.1f} {reduction:.1f}")

    print("\n  TABLE 2: Bus Throughput (transfers/second)")
    print("  " + "-" * 58)
    print(f"  {'Processors':<12} {'Contended':<20} {'Controlled':<20}")
    print("  " + "-" * 58)

    for c, k in zip(contended_results, controlled_results):
        n = c["num_processors"]
        print(f"  {n:<12} {c['throughput']:<20.2f} {k['throughput']:<20.2f}")

    print("\n  TABLE 3: Average Wait Time (seconds)")
    print("  " + "-" * 58)
    print(f"  {'Processors':<12} {'Contended':<20} {'Controlled':<20}")
    print("  " + "-" * 58)

    for c, k in zip(contended_results, controlled_results):
        n = c["num_processors"]
        print(f"  {n:<12} {c['avg_wait']:<20.5f} {k['avg_wait']:<20.5f}")

    print("\n  TABLE 4: Speedup (common baseline = controlled N=1)")
    print("  " + "-" * 58)
    print(f"  {'Processors':<12} {'Contended':<20} {'Controlled':<20} "
          f"{'Ideal'}")
    print("  " + "-" * 58)

    # Single common baseline — controlled N=1
    base = controlled_results[0]["wall_time"]

    for c, k in zip(contended_results, controlled_results):
        n          = c["num_processors"]
        speedup_c  = base / c["wall_time"]
        speedup_k  = base / k["wall_time"]
        print(f"  {n:<12} {speedup_c:<20.4f} {speedup_k:<20.4f} 1.0000")

    print("=" * 82)


# ===============================================================
# PLOT RESULTS
# ===============================================================

def plot_results(contended_results: list,
                 controlled_results: list) -> None:

    n_vals       = [r["num_processors"] for r in contended_results]
    c_times      = [r["wall_time"]      for r in contended_results]
    k_times      = [r["wall_time"]      for r in controlled_results]
    c_times_std  = [r["wall_time_std"]  for r in contended_results]
    k_times_std  = [r["wall_time_std"]  for r in controlled_results]
    c_throughput = [r["throughput"]     for r in contended_results]
    k_throughput = [r["throughput"]     for r in controlled_results]
    c_wait       = [r["avg_wait"]       for r in contended_results]
    k_wait       = [r["avg_wait"]       for r in controlled_results]

    # Ideal: flat line — shared bus wall time cannot decrease with more procs
    ideal_time = [k_times[0]] * len(n_vals)
    ratio       = [c / k for c, k in zip(c_times, k_times)]

    fig = plt.figure(figsize=(15, 11))
    fig.suptitle(
        "Module 3 - Bus & Communication Simulation\n"
        "IE2064 Advanced Computer Organization & Architecture",
        fontsize=15, fontweight="bold", y=0.98
    )

    gs  = gridspec.GridSpec(2, 2, figure=fig, hspace=0.45, wspace=0.35)
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    ax3 = fig.add_subplot(gs[1, 0])
    ax4 = fig.add_subplot(gs[1, 1])

    # (a) Transfer time
    ax1.errorbar(n_vals, c_times, yerr=c_times_std,
                 fmt="o-", color=COLOR_CONTENDED,
                 linewidth=2.2, markersize=8, capsize=5,
                 label="Contended (no control)", zorder=3)
    ax1.errorbar(n_vals, k_times, yerr=k_times_std,
                 fmt="s-", color=COLOR_CONTROLLED,
                 linewidth=2.2, markersize=8, capsize=5,
                 label="Controlled (arbitration)", zorder=3)
    ax1.plot(n_vals, ideal_time, "--",
             color=COLOR_IDEAL, linewidth=1.5,
             label="Single-bus ideal (constant)")

    for i, n in enumerate(n_vals):
        ax1.annotate(f"{c_times[i]:.3f}s", (n, c_times[i]),
                     textcoords="offset points", xytext=(8, 4),
                     fontsize=8, color=COLOR_CONTENDED)
        ax1.annotate(f"{k_times[i]:.3f}s", (n, k_times[i]),
                     textcoords="offset points", xytext=(8, -12),
                     fontsize=8, color=COLOR_CONTROLLED)

    ax1.set_xlabel("Number of Processors", fontsize=11)
    ax1.set_ylabel("Total Wall-Clock Time (seconds)", fontsize=11)
    ax1.set_title("(a) Bus Transfer Time vs Processor Count",
                  fontsize=11, fontweight="bold")
    ax1.legend(fontsize=9)
    ax1.grid(True, linestyle="--", alpha=0.5)
    ax1.set_xticks(n_vals)

    # (b) Overhead ratio
    bar_colors = ["#d62728", "#ff7f0e", "#9467bd", "#8c564b"]
    bars = ax2.bar([str(n) for n in n_vals], ratio,
                   color=bar_colors, edgecolor="black",
                   linewidth=0.8, width=0.5)
    ax2.axhline(y=1.0, color="black", linestyle="--",
                linewidth=1.5, label="Baseline (ratio = 1.0)")

    for bar, r in zip(bars, ratio):
        ax2.text(bar.get_x() + bar.get_width() / 2,
                 bar.get_height() + 0.01,
                 f"{r:.2f}x",
                 ha="center", va="bottom",
                 fontsize=10, fontweight="bold")

    ax2.set_xlabel("Number of Processors", fontsize=11)
    ax2.set_ylabel("Contended Time / Controlled Time", fontsize=11)
    ax2.set_title("(b) Contention Overhead Ratio",
                  fontsize=11, fontweight="bold")
    ax2.legend(fontsize=9)
    ax2.grid(True, axis="y", linestyle="--", alpha=0.5)
    ax2.set_ylim(0, max(ratio) * 1.25)

    # (c) Throughput
    x     = np.arange(len(n_vals))
    width = 0.35

    bars_c = ax3.bar(x - width / 2, c_throughput, width,
                     label="Contended",
                     color=COLOR_CONTENDED,
                     edgecolor="black", linewidth=0.8)
    bars_k = ax3.bar(x + width / 2, k_throughput, width,
                     label="Controlled",
                     color=COLOR_CONTROLLED,
                     edgecolor="black", linewidth=0.8)

    for bar in list(bars_c) + list(bars_k):
        ax3.text(bar.get_x() + bar.get_width() / 2,
                 bar.get_height() + 0.1,
                 f"{bar.get_height():.1f}",
                 ha="center", va="bottom", fontsize=8)

    ax3.set_xlabel("Number of Processors", fontsize=11)
    ax3.set_ylabel("Throughput (transfers / second)", fontsize=11)
    ax3.set_title("(c) Bus Throughput Comparison",
                  fontsize=11, fontweight="bold")
    ax3.set_xticks(x)
    ax3.set_xticklabels([str(n) for n in n_vals])
    ax3.legend(fontsize=9)
    ax3.grid(True, axis="y", linestyle="--", alpha=0.5)

    # (d) Wait time
    ax4.plot(n_vals, [w * 1000 for w in c_wait],
             "o-", color=COLOR_CONTENDED,
             linewidth=2.2, markersize=8,
             label="Contended wait time")
    ax4.plot(n_vals, [w * 1000 for w in k_wait],
             "s-", color=COLOR_CONTROLLED,
             linewidth=2.2, markersize=8,
             label="Controlled wait time")
    ax4.fill_between(n_vals,
                     [w * 1000 for w in c_wait],
                     [w * 1000 for w in k_wait],
                     alpha=0.15, color="orange",
                     label="Wait time reduction")

    ax4.set_xlabel("Number of Processors", fontsize=11)
    ax4.set_ylabel("Average Wait Time per Transfer (ms)", fontsize=11)
    ax4.set_title("(d) Average Wait Time per Transfer",
                  fontsize=11, fontweight="bold")
    ax4.legend(fontsize=9)
    ax4.grid(True, linestyle="--", alpha=0.5)
    ax4.set_xticks(n_vals)

    plt.savefig("module3_bus_communication.png",
                dpi=150, bbox_inches="tight")
    print("\n[Module 3] Graph saved -> module3_bus_communication.png")
    plt.show()


# ===============================================================
# ANALYSIS SUMMARY
# ===============================================================

def print_analysis(contended_results: list,
                   controlled_results: list) -> None:

    c8 = contended_results[-1]
    k8 = controlled_results[-1]

    overhead_8  = ((c8["wall_time"] - k8["wall_time"])
                   / k8["wall_time"]) * PERCENT
    reduction_8 = ((c8["wall_time"] - k8["wall_time"])
                   / c8["wall_time"]) * PERCENT

    print(f"""
  ANALYSIS & DISCUSSION
  {'=' * 78}

  THEORETICAL PREDICTION:
  A single shared bus is a serial bottleneck. Maximum speedup = 1.0
  regardless of processor count (Amdahl's Law, serial fraction = 1.0).

  SIMULATION FINDINGS (8 processors):
    Contended bus time  : {c8['wall_time']:.4f}s
    Controlled bus time : {k8['wall_time']:.4f}s
    Overhead at N=8     : {overhead_8:.1f}%
    Time reduction      : {reduction_8:.1f}%

  CONCLUSION:
    Shared bus is suitable only for small multiprocessor systems (≤8).
    Arbitration improves efficiency but cannot overcome serial bottleneck.
    Scalable interconnects (crossbar, mesh, point-to-point) required
    for larger systems.
    """)


# ===============================================================
# MAIN
# ===============================================================

def module3_main() -> None:
    print("\n" + "=" * 82)
    print("  MODULE 3 - Bus & Communication Simulation")
    print("  IE2064 Advanced Computer Organization & Architecture")
    print("=" * 82)

    contended_results, controlled_results = collect_results()
    print_results_table(contended_results, controlled_results)
    print_analysis(contended_results, controlled_results)
    plot_results(contended_results, controlled_results)


if __name__ == "__main__":
    module3_main()
    
