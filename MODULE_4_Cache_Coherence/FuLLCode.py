import multiprocessing as mp
import time
import pandas as pd
import matplotlib.pyplot as plt

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


# =========================
# MAIN
# =========================
if __name__ == "__main__":

    results = run_tests()

    analyze(results)

    plot_execution_times(results)
    plot_speedup(results)