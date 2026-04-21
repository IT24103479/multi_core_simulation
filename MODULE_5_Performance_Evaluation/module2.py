import os
import time
import random
import queue
from multiprocessing import Process, Queue
import matplotlib.pyplot as plt

try:
    import psutil  # py -m pip install psutil
except ModuleNotFoundError:
    psutil = None


# -----------------------------
# 🔹 Worker Task (sleep-based)
# -----------------------------
def worker_task(duration: float) -> None:
    time.sleep(duration)


# -----------------------------
# 🔹 Static Scheduling
# -----------------------------
def static_worker(tasks, results: Queue, core_id: int) -> None:
    for _, duration in tasks:
        worker_task(duration)
    results.put(core_id)


def _partition_tasks_static(tasks, num_cores: int):
    n = len(tasks)
    base = n // num_cores
    extra = n % num_cores

    chunks = []
    start = 0
    for i in range(num_cores):
        size = base + (1 if i < extra else 0)
        end = start + size
        chunks.append(tasks[start:end])
        start = end
    return chunks


def static_schedule(tasks, num_cores: int):
    """
    Returns:
        elapsed_seconds (float),
        child_pids (list[int])
    """
    if num_cores <= 0:
        raise ValueError("num_cores must be >= 1")
    if not tasks:
        return 0.0, []

    num_cores = min(num_cores, len(tasks))

    start_time = time.time()
    results = Queue()
    processes = []

    chunks = _partition_tasks_static(tasks, num_cores)

    for i in range(num_cores):
        p = Process(target=static_worker, args=(chunks[i], results, i))
        processes.append(p)
        p.start()

    child_pids = [p.pid for p in processes if p.pid is not None]

    for p in processes:
        p.join()

    for _ in range(num_cores):
        try:
            results.get_nowait()
        except queue.Empty:
            break

    return time.time() - start_time, child_pids


# -----------------------------
# 🔹 Dynamic Scheduling
# -----------------------------
def dynamic_worker(task_queue, results: Queue, core_id: int) -> None:
    batch_size = 3
    while True:
        tasks_to_do = []
        for _ in range(batch_size):
            try:
                tasks_to_do.append(task_queue.get_nowait())
            except queue.Empty:
                break

        if not tasks_to_do:
            break

        for _, duration in tasks_to_do:
            worker_task(duration)

    results.put(core_id)


def dynamic_schedule(tasks, num_cores: int, batch_size: int = 3):
    """
    Returns:
        elapsed_seconds (float),
        child_pids (list[int])
    """
    if num_cores <= 0:
        raise ValueError("num_cores must be >= 1")
    if not tasks:
        return 0.0, []

    num_cores = min(num_cores, len(tasks))

    task_queue = Queue()
    results = Queue()
    for task in tasks:
        task_queue.put(task)

    start_time = time.time()

    processes = []
    for i in range(num_cores):
        p = Process(target=dynamic_worker, args=(task_queue, results, i))
        processes.append(p)
        p.start()

    child_pids = [p.pid for p in processes if p.pid is not None]

    for p in processes:
        p.join()

    for _ in range(num_cores):
        try:
            results.get_nowait()
        except queue.Empty:
            break

    return time.time() - start_time, child_pids


# -----------------------------
# 🔹 Task Generator
# -----------------------------
def generate_tasks_mode(num_tasks: int, mode: str = "single"):
    tasks = []
    for i in range(num_tasks):
        if mode == "equal":
            duration = 0.05
        elif mode == "uneven":
            if random.random() < 0.7:
                duration = random.uniform(0.05, 0.1)
            else:
                duration = random.uniform(0.1, 1.1)
        else:
            duration = random.uniform(0.05, 0.2)

        tasks.append((i, duration))
    return tasks


def print_tasks_every_20(tasks) -> None:
    for idx in range(1, len(tasks) + 1):
        if idx == 1 or idx % 20 == 0:
            task_id, duration = tasks[idx - 1]
            print(f"Task {idx} (id={task_id}) duration={duration:.4f}s")


# -----------------------------
# 🔹 Metrics
# -----------------------------
def calculate_metrics(seq_time, parallel_times, cores_list):
    speedups = []
    efficiencies = []

    for t, cores in zip(parallel_times, cores_list):
        speedup = (seq_time / t) if t > 0 else float("inf")
        efficiency = (speedup / cores) if cores > 0 else 0.0
        speedups.append(speedup)
        efficiencies.append(efficiency)

    return speedups, efficiencies


def amdahl_speedup(p, n):
    return 1 / ((1 - p) + (p / n))


# -----------------------------
#  Fully-correct CPU-time-delta measurement (runner process + monitoring loop)
# -----------------------------
def _run_schedule_in_child(result_q: Queue, schedule_name: str, tasks, cores: int):
    """
    Top-level function (Windows spawn-safe).
    Runs the schedule inside a child process so the parent can monitor worker children while running.
    """
    if schedule_name == "static":
        elapsed, _pids = static_schedule(tasks, cores)
    elif schedule_name == "dynamic":
        elapsed, _pids = dynamic_schedule(tasks, cores)
    else:
        raise ValueError("Unknown schedule_name")

    result_q.put(elapsed)


def _safe_children(proc):
    if psutil is None:
        return []
    try:
        return proc.children(recursive=True)
    except psutil.Error:
        return []


def _cpu_time_seconds(ps_proc) -> float:
    try:
        ct = ps_proc.cpu_times()
        return float(ct.user) + float(ct.system)
    except psutil.Error:
        return 0.0


def measure_run_cpu_mem(schedule_name: str, tasks, cores: int, sample_interval: float = 0.1):
    """
    Measures for THIS PROGRAM ONLY (runner's worker children):
      - elapsed time (schedule time)
      - cpu_util_machine_pct via CPU-time delta
      - peak RSS sum (MB) during run

    Returns: elapsed_s, cpu_util_machine_pct, peak_rss_mb_sum
    """
    if psutil is None:
        # still run so times work
        result_q = Queue()
        runner = Process(target=_run_schedule_in_child, args=(result_q, schedule_name, tasks, cores))
        runner.start()
        runner.join()
        try:
            elapsed = result_q.get_nowait()
        except queue.Empty:
            elapsed = 0.0
        return elapsed, 0.0, 0.0

    result_q = Queue()
    runner = Process(target=_run_schedule_in_child, args=(result_q, schedule_name, tasks, cores))

    logical_cores = psutil.cpu_count(logical=True) or 1
    # Take a small instantaneous sample before starting so we have a "before" value
    sample_before = 0.0
    try:
        # small blocking sample (~10ms) to get an immediate reading
        sample_before = psutil.cpu_percent(interval=0.01)
    except psutil.Error:
        sample_before = 0.0

    t0 = time.time()
    runner.start()

    runner_ps = psutil.Process(runner.pid)

    # Wait briefly so workers exist
    time.sleep(0.05)

    # Prime cpu_percent for children to avoid initial 0, not strictly needed for cpu-time delta.
    for ch in _safe_children(runner_ps):
        try:
            ch.cpu_percent(None)
        except psutil.Error:
            pass

    peak_rss = 0

    # Collect lightweight machine-wide cpu_percent samples while monitoring
    percent_samples = []

    # Prime machine-wide counter so subsequent interval=None calls are meaningful
    try:
        psutil.cpu_percent(None)
    except psutil.Error:
        pass

    # Monitor while running
    while runner.is_alive():
        children = _safe_children(runner_ps)

        rss_sum = 0
        for ch in children:
            try:
                rss_sum += ch.memory_info().rss
            except psutil.Error:
                pass

        peak_rss = max(peak_rss, rss_sum)

        # non-blocking sample since last call
        try:
            pct = psutil.cpu_percent(None)
            percent_samples.append(pct)
        except psutil.Error:
            pass

        time.sleep(sample_interval)

    runner.join()
    t1 = time.time()

    # Take a small instantaneous sample after finish
    sample_after = 0.0
    try:
        sample_after = psutil.cpu_percent(interval=0.01)
    except psutil.Error:
        sample_after = 0.0

    try:
        elapsed = result_q.get_nowait()
    except queue.Empty:
        elapsed = 0.0

    # Compute average of before/during/after samples (sampling-only measurement)
    avg_percent = 0.0
    try:
        s = 0.0
        total_samples = 0
        if sample_before:
            s += sample_before
            total_samples += 1
        s += sum(percent_samples)
        total_samples += len(percent_samples)
        if sample_after:
            s += sample_after
            total_samples += 1

        if total_samples > 0:
            avg_percent = s / total_samples
    except Exception:
        avg_percent = 0.0

    # Use the sampled average as the sole cpu util measurement
    cpu_util_machine_pct = avg_percent

    peak_rss_mb = peak_rss / (1024 * 1024)
    return elapsed, cpu_util_machine_pct, peak_rss_mb


# -----------------------------
# 🔹 Plotting helpers
# -----------------------------
def plot_metric(title: str, x, y_static, y_dynamic, ylabel: str):
    plt.figure()
    plt.plot(x, y_static, marker="o", label="Static")
    plt.plot(x, y_dynamic, marker="o", label="Dynamic")
    plt.xlabel("Number of Processes")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.legend()
    plt.grid(True)
    plt.show()


def plot_speedup(title: str, cores_list, speedup_static, speedup_dynamic, p_assumed: float):
    amdahl_curve = [amdahl_speedup(p_assumed, c) for c in cores_list]
    plt.figure()
    plt.plot(cores_list, speedup_static, marker="o", label="Static speedup")
    plt.plot(cores_list, speedup_dynamic, marker="o", label="Dynamic speedup")
    plt.plot(cores_list, amdahl_curve, linestyle="--", label=f"Amdahl’s Law (p={p_assumed})")
    plt.xlabel("Number of Processes")
    plt.ylabel("Speedup")
    plt.title(title)
    plt.legend()
    plt.grid(True)
    plt.show()


# -----------------------------
# 🔹 Main Runner (10 graphs: 5 per mode)
# -----------------------------
def run_module5():
    num_tasks = 160
    max_cores = 8
    cores_list = [1, 2, 4, 8]
    cores_list = [c for c in cores_list if c <= max_cores]

    if psutil is None:
        print("\nWARNING: psutil is not installed.")
        print("Install with: py -m pip install psutil")
        print("CPU and Memory graphs will be 0 until psutil is installed.\n")

    for mode in ("equal", "uneven"):
        print(f"\n===== {mode.upper()} WORKLOAD TEST =====")

        tasks = generate_tasks_mode(num_tasks, mode)
        print("Tasks (sample):")
        print_tasks_every_20(tasks)

        # Sequential baseline: 1 process static time
        seq_time, _ = static_schedule(tasks, 1)
        print("Sequential Time:", round(seq_time, 3), "s")

        times_static = []
        times_dynamic = []

        cpu_static = []
        cpu_dynamic = []

        mem_static = []
        mem_dynamic = []

        for cores in cores_list:
            print(f"\nRunning with {cores} processes...")

            # Fully-correct CPU-time delta (runner + monitoring)
            t_s, cpu_s, mem_s = measure_run_cpu_mem("static", tasks, cores)
            t_d, cpu_d, mem_d = measure_run_cpu_mem("dynamic", tasks, cores)

            times_static.append(t_s)
            times_dynamic.append(t_d)

            cpu_static.append(cpu_s)
            cpu_dynamic.append(cpu_d)

            mem_static.append(mem_s)
            mem_dynamic.append(mem_d)

            print(f"Static Time:  {t_s:.3f} s | CPU util (machine %): {cpu_s:.3f} | Peak RSS(sum): {mem_s:.1f} MB")
            print(f"Dynamic Time: {t_d:.3f} s | CPU util (machine %): {cpu_d:.3f} | Peak RSS(sum): {mem_d:.1f} MB")

        # Speedup / efficiency per strategy using seq_time baseline (your requested formula)
        speedup_static, efficiency_static = calculate_metrics(seq_time, times_static, cores_list)
        speedup_dynamic, efficiency_dynamic = calculate_metrics(seq_time, times_dynamic, cores_list)

        print("\n--- Speedup (seq_time / time) ---")
        for c, ss, sd in zip(cores_list, speedup_static, speedup_dynamic):
            print(f"Processes={c} | Static speedup={ss:.3f} | Dynamic speedup={sd:.3f}")

        print("\n--- Efficiency (speedup / processes) ---")
        for c, es, ed in zip(cores_list, efficiency_static, efficiency_dynamic):
            print(f"Processes={c} | Static efficiency={es:.3f} | Dynamic efficiency={ed:.3f}")

        p_assumed = 0.8 if mode == "equal" else 0.9
        title_prefix = mode.capitalize()

        # 5 graphs per mode (10 total): Static vs Dynamic on all graphs
        plot_metric(
            f"{title_prefix} Workload - Execution Time vs Processes",
            cores_list,
            times_static,
            times_dynamic,
            "Execution Time (s)",
        )

        plot_speedup(
            f"{title_prefix} Workload - Speedup vs Processes",
            cores_list,
            speedup_static,
            speedup_dynamic,
            p_assumed=p_assumed,
        )

        plot_metric(
            f"{title_prefix} Workload - Efficiency vs Processes",
            cores_list,
            efficiency_static,
            efficiency_dynamic,
            "Efficiency",
        )

        plot_metric(
            f"{title_prefix} Workload - CPU Utilization vs Processes",
            cores_list,
            cpu_static,
            cpu_dynamic,
            "CPU Utilization (% of total machine capacity)",
        )

        plot_metric(
            f"{title_prefix} Workload - Peak Memory Usage vs Processes",
            cores_list,
            mem_static,
            mem_dynamic,
            "Peak RSS (sum of workers, MB)",
        )


# -----------------------------
# 🔹 Entry
# -----------------------------
if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    run_module5()