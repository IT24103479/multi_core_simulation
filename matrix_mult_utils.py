import os
import time
import threading
import multiprocessing

import matplotlib.pyplot as plt
import numpy as np

try:
    import psutil  # py -m pip install psutil
except ModuleNotFoundError:
    psutil = None


# Matrix size (increase if needed for clearer results)
SIZE = 1500

# Generate matrices
A = np.random.rand(SIZE, SIZE)
B = np.random.rand(SIZE, SIZE)


# -------------------------------
# 1. Sequential Matrix Multiplication
# -------------------------------
def sequential_multiply(A, B):
    return np.dot(A, B)


# -------------------------------
# 2. Multithreading Implementation
# -------------------------------
def thread_worker(A, B, result, start, end):
    result[start:end] = np.dot(A[start:end], B)


def threaded_multiply(A, B, num_threads):
    threads = []
    result = np.zeros((A.shape[0], B.shape[1]))

    step = A.shape[0] // num_threads

    for i in range(num_threads):
        start = i * step
        end = (i + 1) * step if i != num_threads - 1 else A.shape[0]

        t = threading.Thread(target=thread_worker, args=(A, B, result, start, end))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    return result


# -------------------------------
# 3. Multiprocessing Implementation
# -------------------------------
def process_worker(args):
    A_part, B = args
    return np.dot(A_part, B)


def multiprocessing_multiply(A, B, num_processes):
    pool = multiprocessing.Pool(processes=num_processes)

    step = A.shape[0] // num_processes
    chunks = []

    for i in range(num_processes):
        start = i * step
        end = (i + 1) * step if i != num_processes - 1 else A.shape[0]
        chunks.append((A[start:end], B))

    results = pool.map(process_worker, chunks)
    pool.close()
    pool.join()

    return np.vstack(results)


# -------------------------------
# 4. Performance Measurement
# -------------------------------
def measure_time(func, *args):
    start = time.time()
    func(*args)
    end = time.time()
    return end - start


def _safe_children(proc):
    if psutil is None:
        return []
    try:
        return proc.children(recursive=True)
    except psutil.Error:
        return []


def measure_run_cpu_mem(func, *args, include_children=False, sample_interval=0.1):
    start = time.time()

    if psutil is None:
        func(*args)
        end = time.time()
        return end - start, 0.0, 0.0

    current_process = psutil.Process(os.getpid())

    sample_before = 0.0
    try:
        sample_before = psutil.cpu_percent(interval=0.01)
    except psutil.Error:
        sample_before = 0.0

    cpu_samples = []
    peak_rss = [0]
    stop_event = threading.Event()

    def sampler():
        try:
            psutil.cpu_percent(None)
        except psutil.Error:
            pass

        while not stop_event.is_set():
            try:
                cpu_samples.append(psutil.cpu_percent(None))
            except psutil.Error:
                pass

            rss_sum = 0
            if include_children:
                for child in _safe_children(current_process):
                    try:
                        rss_sum += child.memory_info().rss
                    except psutil.Error:
                        pass
            else:
                try:
                    rss_sum = current_process.memory_info().rss
                except psutil.Error:
                    rss_sum = 0

            if rss_sum > peak_rss[0]:
                peak_rss[0] = rss_sum

            time.sleep(sample_interval)

    sampling_thread = threading.Thread(target=sampler, daemon=True)
    sampling_thread.start()

    func(*args)

    stop_event.set()
    sampling_thread.join()

    end = time.time()

    sample_after = 0.0
    try:
        sample_after = psutil.cpu_percent(interval=0.01)
    except psutil.Error:
        sample_after = 0.0

    avg_cpu = 0.0
    try:
        total = 0.0
        count = 0

        if sample_before:
            total += sample_before
            count += 1

        total += sum(cpu_samples)
        count += len(cpu_samples)

        if sample_after:
            total += sample_after
            count += 1

        if count > 0:
            avg_cpu = total / count
    except Exception:
        avg_cpu = 0.0

    peak_rss_mb = peak_rss[0] / (1024 * 1024)
    return end - start, avg_cpu, peak_rss_mb


# -------------------------------
# 5. Plotting / Metrics Helpers
# -------------------------------
def calculate_metrics(seq_time, parallel_times, workers_list):
    speedups = []
    efficiencies = []

    for t, workers in zip(parallel_times, workers_list):
        speedup = (seq_time / t) if t > 0 else float("inf")
        efficiency = (speedup / workers) if workers > 0 else 0.0
        speedups.append(speedup)
        efficiencies.append(efficiency)

    return speedups, efficiencies


def amdahl_speedup(p, n):
    return 1 / ((1 - p) + (p / n))


def plot_metric(title, workers, y_threading, y_multiprocessing, ylabel):
    plt.figure()
    plt.plot(workers, y_threading, marker="o", label="Threading")
    plt.plot(workers, y_multiprocessing, marker="o", label="Multiprocessing")
    plt.xlabel("Number of Workers")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.legend()
    plt.grid(True)
    plt.show()


def plot_speedup(title, workers, speedup_threading, speedup_multiprocessing, p_assumed):
    amdahl_curve = [amdahl_speedup(p_assumed, w) for w in workers]

    plt.figure()
    plt.plot(workers, speedup_threading, marker="o", label="Threading speedup")
    plt.plot(workers, speedup_multiprocessing, marker="o", label="Multiprocessing speedup")
    plt.plot(workers, amdahl_curve, linestyle="--", label=f"Amdahl's Law (p={p_assumed})")
    plt.xlabel("Number of Workers")
    plt.ylabel("Speedup")
    plt.title(title)
    plt.legend()
    plt.grid(True)
    plt.show()


# -------------------------------
# 6. Main Execution
# -------------------------------
if __name__ == "__main__":
    print("Running Matrix Multiplication Tests...\n")

    # Sequential
    seq_time = measure_time(sequential_multiply, A, B)
    print(f"Sequential Time: {seq_time:.4f} seconds")

    results = []

    threads_list = [2, 4, 8]
    processes_list = [2, 4, 8]

    threading_times = []
    threading_cpu = []
    threading_mem = []

    multiprocessing_times = []
    multiprocessing_cpu = []
    multiprocessing_mem = []

    # Threading Tests
    for threads in threads_list:
        t_time, t_cpu, t_mem = measure_run_cpu_mem(threaded_multiply, A, B, threads, include_children=False)
        speedup = seq_time / t_time
        efficiency = speedup / threads

        threading_times.append(t_time)
        threading_cpu.append(t_cpu)
        threading_mem.append(t_mem)

        results.append(("Threading", threads, t_time, speedup, efficiency))
        print(f"Threading ({threads} threads): {t_time:.4f}s | Speedup: {speedup:.2f} | Efficiency: {efficiency:.2f}")

    # Multiprocessing Tests
    for processes in processes_list:
        p_time, p_cpu, p_mem = measure_run_cpu_mem(
            multiprocessing_multiply,
            A,
            B,
            processes,
            include_children=True,
        )
        speedup = seq_time / p_time
        efficiency = speedup / processes

        multiprocessing_times.append(p_time)
        multiprocessing_cpu.append(p_cpu)
        multiprocessing_mem.append(p_mem)

        results.append(("Multiprocessing", processes, p_time, speedup, efficiency))
        print(f"Multiprocessing ({processes} processes): {p_time:.4f}s | Speedup: {speedup:.2f} | Efficiency: {efficiency:.2f}")

    print("\n--- Summary Table ---")
    print("Method | Workers | Time | Speedup | Efficiency")

    for r in results:
        print(f"{r[0]} | {r[1]} | {r[2]:.4f} | {r[3]:.2f} | {r[4]:.2f}")

    workers_axis = threads_list

    speedup_threading, efficiency_threading = calculate_metrics(seq_time, threading_times, threads_list)
    speedup_multiprocessing, efficiency_multiprocessing = calculate_metrics(seq_time, multiprocessing_times, processes_list)

    p_assumed = 0.9

    plot_metric(
        "Execution Time vs Workers",
        workers_axis,
        threading_times,
        multiprocessing_times,
        "Execution Time (s)",
    )

    plot_speedup(
        "Speedup vs Workers",
        workers_axis,
        speedup_threading,
        speedup_multiprocessing,
        p_assumed,
    )

    plot_metric(
        "Efficiency vs Workers",
        workers_axis,
        efficiency_threading,
        efficiency_multiprocessing,
        "Efficiency",
    )

    plot_metric(
        "CPU Utilization vs Workers",
        workers_axis,
        threading_cpu,
        multiprocessing_cpu,
        "CPU Utilization (% of total machine capacity)",
    )

    plot_metric(
        "Peak Memory Usage vs Workers",
        workers_axis,
        threading_mem,
        multiprocessing_mem,
        "Peak RSS (MB)",
    )
