import multiprocessing as mp
import time
import pandas as pd
import matplotlib.pyplot as plt
import psutil
import os

if __name__ == "__main__":
    mp.freeze_support()

# =========================
# CONFIG
# =========================
ITERATIONS = 1_000_000


# =========================
# 1. BASELINE (NO SHARING)
# =========================
def baseline_worker():
    x = 0
    for _ in range(ITERATIONS):
        x += 1


# =========================
# 2. FALSE SHARING
# =========================
def false_sharing_worker(arr, index):
    for _ in range(ITERATIONS):
        arr[index] += 1


# =========================
# 3. PADDED (CACHE-FRIENDLY)
# =========================
def padded_worker(counter):
    for _ in range(ITERATIONS):
        counter.value += 1


# =========================
# 4. TRUE SHARING (LOCKED)
# =========================
def true_sharing_worker(counter, lock):
    for _ in range(ITERATIONS):
        with lock:
            counter.value += 1


# =========================
# RUN TEST FUNCTION
# =========================
def run_tests():

    results = {}

    # ---------- BASELINE ----------
    start = time.perf_counter()

    p1 = mp.Process(target=baseline_worker)
    p2 = mp.Process(target=baseline_worker)

    p1.start(); p2.start()
    p1.join(); p2.join()

    results["Baseline"] = time.perf_counter() - start


    # ---------- FALSE SHARING ----------
    arr = mp.Array('i', 2)

    start = time.perf_counter()

    p1 = mp.Process(target=false_sharing_worker, args=(arr, 0))
    p2 = mp.Process(target=false_sharing_worker, args=(arr, 1))

    p1.start(); p2.start()
    p1.join(); p2.join()

    results["False Sharing"] = time.perf_counter() - start


    # ---------- PADDED ----------
    c1 = mp.Value('i', 0)
    c2 = mp.Value('i', 0)

    start = time.perf_counter()

    p1 = mp.Process(target=padded_worker, args=(c1,))
    p2 = mp.Process(target=padded_worker, args=(c2,))

    p1.start(); p2.start()
    p1.join(); p2.join()

    results["Padded"] = time.perf_counter() - start


    # ---------- TRUE SHARING ----------
    counter = mp.Value('i', 0)
    lock = mp.Lock()

    start = time.perf_counter()

    p1 = mp.Process(target=true_sharing_worker, args=(counter, lock))
    p2 = mp.Process(target=true_sharing_worker, args=(counter, lock))

    p1.start(); p2.start()
    p1.join(); p2.join()

    results["True Sharing"] = time.perf_counter() - start

    return results


# =========================
# ANALYSIS TABLE
# =========================
def analyze(results):

    df = pd.DataFrame.from_dict(results, orient='index', columns=['Time (s)'])

    baseline = df.loc["Baseline", "Time (s)"]

    df["Relative"] = df["Time (s)"] / baseline
    df["Speedup"] = baseline / df["Time (s)"]

    print("\n===== FINAL RESULTS =====\n")
    print(df)

    print("\nFalse Sharing Penalty:",
          round(results["False Sharing"] / results["Baseline"], 2), "x")


# =========================
# GRAPH 1: EXECUTION TIME
# =========================
def plot_execution_times(results):

    plt.figure()
    plt.bar(results.keys(), results.values())

    plt.title("Execution Time Comparison")
    plt.xlabel("Scenario")
    plt.ylabel("Time (seconds)")
    plt.xticks(rotation=20)

    plt.tight_layout()
    plt.show()


# =========================
# GRAPH 2: SPEEDUP
# =========================
def plot_speedup(results):

    baseline = results["Baseline"]

    speedup = {k: baseline / v for k, v in results.items()}

    plt.figure()
    plt.bar(speedup.keys(), speedup.values())

    plt.title("Speedup vs Baseline")
    plt.xlabel("Scenario")
    plt.ylabel("Speedup (Higher is Better)")
    plt.xticks(rotation=20)

    plt.tight_layout()
    plt.show()

    
# ============================================================
# MODULE 5 - PERFORMANCE METRICS (SCALING + ALL SCENARIOS)
# ============================================================



PROCESS_COUNTS = [1, 2]


# =========================
# SHARED SETUPS FOR EACH CASE
# =========================
def setup_baseline(p):
    return [tuple() for _ in range(p)]


def setup_false_sharing(p):
    arr = mp.Array('i', p)
    return [(arr, i) for i in range(p)]


def setup_padded(p):
    return [(mp.Value('i', 0),) for _ in range(p)]


def setup_true_sharing(p):
    counter = mp.Value('i', 0)
    lock = mp.Lock()
    return [(counter, lock) for _ in range(p)]


# =========================
# SCALING TEST
# =========================
def run_scaling(worker_func, setup_func):

    exec_times = []
    cpu_usage = []
    memory_usage = []

    for p_count in PROCESS_COUNTS:

        processes = []
        shared_args = setup_func(p_count)

        start_mem = psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)

        start = time.perf_counter()

        for i in range(p_count):
            p = mp.Process(target=worker_func, args=shared_args[i])
            processes.append(p)
            p.start()

        # CPU usage during execution
        cpu = psutil.cpu_percent(interval=None)

        for p in processes:
            p.join()

        end = time.perf_counter()
        end_mem = psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)

        exec_times.append(end - start)
        cpu_usage.append(cpu)
        memory_usage.append(end_mem - start_mem)

    return exec_times, cpu_usage, memory_usage


# =========================
# METRICS
# =========================
def compute_metrics(exec_times):
    t1 = exec_times[0]
    speedup = [t1 / t for t in exec_times]
    efficiency = [s / p for s, p in zip(speedup, PROCESS_COUNTS)]
    return speedup, efficiency


# =========================
# AMDahl’s Law
# =========================
def amdahl(p, n):
    return 1 / ((1 - p) + (p / n))


def amdahl_curve(p=0.1):
    return [amdahl(p, n) for n in PROCESS_COUNTS]


# =========================
# RUN ALL SCENARIOS
# =========================
def run_module5():

    scenarios = {
        "Baseline": (baseline_worker, setup_baseline),
        "False Sharing": (false_sharing_worker, setup_false_sharing),
        "Padded": (padded_worker, setup_padded),
        "True Sharing": (true_sharing_worker, setup_true_sharing),
    }

    results = {}

    for name, (worker, setup) in scenarios.items():
        print(f"\nRunning {name}...")
        exec_t, cpu, mem = run_scaling(worker, setup)
        speedup, efficiency = compute_metrics(exec_t)

        # =========================
        # PRINT RESULTS (NEW)
        # =========================
        print(f"\n--- {name} ---")
        print("Processes     :", PROCESS_COUNTS)
        print("Execution Time:", [round(t, 4) for t in exec_t])
        print("Speedup       :", [round(s, 4) for s in speedup])
        print("Efficiency    :", [round(e, 4) for e in efficiency])
        print("CPU Usage (%) :", [round(c, 2) for c in cpu])
        print("Memory (MB)   :", [round(m, 4) for m in mem])

        # =========================
        # STORE RESULTS
        # =========================
        results[name] = {
            "exec": exec_t,
            "cpu": cpu,
            "mem": mem,
            "speedup": speedup,
            "eff": efficiency
        }

    return results


# =========================
# PLOTTING
# =========================
def plot_all(results):

    # -------- Execution Time --------
    plt.figure()
    for name in results:
        plt.plot(PROCESS_COUNTS, results[name]["exec"], marker='o', label=name)
        
    # Add sequential reference line (NEW)
    sequential_time = results["Baseline"]["exec"][0]
    plt.axhline(y=sequential_time, linestyle='--', label="Sequential")

    plt.title("Execution Time vs Processes")
    plt.xlabel("Processes")
    plt.ylabel("Time (s)")
    plt.legend()
    plt.grid()
    plt.show()

    # -------- Speedup + Amdahl --------
    plt.figure()
    for name in results:
        plt.plot(PROCESS_COUNTS, results[name]["speedup"], marker='o', label=name)

    plt.plot(PROCESS_COUNTS, amdahl_curve(), linestyle='--', label="Amdahl (p=0.1)")

    plt.title("Speedup vs Processes")
    plt.xlabel("Processes")
    plt.ylabel("Speedup")
    plt.legend()
    plt.grid()
    plt.show()

    # -------- Efficiency --------
    plt.figure()
    for name in results:
        plt.plot(PROCESS_COUNTS, results[name]["eff"], marker='o', label=name)

    plt.title("Efficiency vs Processes")
    plt.xlabel("Processes")
    plt.ylabel("Efficiency")
    plt.legend()
    plt.grid()
    plt.show()

    # -------- CPU --------
    plt.figure()
    for name in results:
        plt.plot(PROCESS_COUNTS, results[name]["cpu"], marker='o', label=name)

    plt.title("CPU Utilisation vs Processes")
    plt.xlabel("Processes")
    plt.ylabel("CPU (%)")
    plt.legend()
    plt.grid()
    plt.show()

    # -------- Memory --------
    plt.figure()
    for name in results:
        plt.plot(PROCESS_COUNTS, results[name]["mem"], marker='o', label=name)

    plt.title("Memory Usage vs Processes")
    plt.xlabel("Processes")
    plt.ylabel("Memory (MB)")
    plt.legend()
    plt.grid()
    plt.show()



# =========================
# MAIN
# =========================
if __name__ == "__main__":

    results = run_tests()

    analyze(results)

    plot_execution_times(results)
    plot_speedup(results)
    
    # =========================
    # EXECUTE MODULE 5
    # =========================
    print("\n===== MODULE 5 PERFORMANCE =====")

    module5_results = run_module5()

    plot_all(module5_results)
