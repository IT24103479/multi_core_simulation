import multiprocessing as mp
import time
import matplotlib.pyplot as plt

ITERATIONS = 1_000_000


# =================================================
# 1. WORKER FUNCTIONS
# =================================================

def baseline_worker():
    """No sharing, independent computation"""
    x = 0
    for _ in range(ITERATIONS):
        x += 1


def false_sharing_worker(arr, index):
    """Different variables but likely same cache line"""
    for _ in range(ITERATIONS):
        arr[index] += 1


def padded_worker(arr, index):
    """Cache-line separated access"""
    for _ in range(ITERATIONS):
        arr[index] += 1


def true_sharing_worker(counter):
    """
    True sharing:
    Both processes modify SAME variable
    Causes cache line invalidation traffic (MESI)
    """
    for _ in range(ITERATIONS):
        counter.value += 1


# =================================================
# 2. RUN EXPERIMENTS
# =================================================

def run_tests():
    results = {}

    # ---------------- BASELINE ----------------
    start = time.time()

    p1 = mp.Process(target=baseline_worker)
    p2 = mp.Process(target=baseline_worker)

    p1.start(); p2.start()
    p1.join(); p2.join()

    results["Baseline"] = time.time() - start


    # ---------------- FALSE SHARING ----------------
    arr = mp.Array('i', 2)   # likely same cache line

    start = time.time()

    p1 = mp.Process(target=false_sharing_worker, args=(arr, 0))
    p2 = mp.Process(target=false_sharing_worker, args=(arr, 1))

    p1.start(); p2.start()
    p1.join(); p2.join()

    results["False Sharing"] = time.time() - start


    # ---------------- PADDED (CACHE LINE FIX) ----------------
    # 64 ints ≈ separate cache lines
    arr = mp.Array('i', 64)

    start = time.time()

    p1 = mp.Process(target=padded_worker, args=(arr, 0))
    p2 = mp.Process(target=padded_worker, args=(arr, 32))

    p1.start(); p2.start()
    p1.join(); p2.join()

    results["Padded"] = time.time() - start


    # ---------------- TRUE SHARING ----------------
    counter = mp.Value('i', 0)

    start = time.time()

    p1 = mp.Process(target=true_sharing_worker, args=(counter,))
    p2 = mp.Process(target=true_sharing_worker, args=(counter,))

    p1.start(); p2.start()
    p1.join(); p2.join()

    results["True Sharing"] = time.time() - start

    return results, counter


# =================================================
# 3. VISUALIZATION
# =================================================

def plot_execution_times(results):
    plt.figure()
    plt.bar(results.keys(), results.values())
    plt.title("Execution Time vs Cache Coherence Scenario")
    plt.xlabel("Scenario")
    plt.ylabel("Time (seconds)")
    plt.xticks(rotation=20)
    plt.tight_layout()
    plt.show()


def plot_speedup(results):
    baseline = results["Baseline"]
    speedup = {k: baseline / v for k, v in results.items()}

    plt.figure()
    plt.bar(speedup.keys(), speedup.values())
    plt.title("Speedup Compared to Baseline")
    plt.xlabel("Scenario")
    plt.ylabel("Speedup Factor")
    plt.xticks(rotation=20)
    plt.tight_layout()
    plt.show()


# =================================================
# 4. MAIN
# =================================================

if __name__ == "__main__":

    results, counter = run_tests()

    print("\n===== PERFORMANCE RESULTS =====")
    for k, v in results.items():
        print(f"{k}: {v:.4f} seconds")

    print("\nFinal True Sharing Counter Value:", counter.value)

    # ---------------- PENALTY ANALYSIS ----------------
    penalty = results["False Sharing"] / results["Baseline"]
    print(f"\nFalse Sharing Penalty: {penalty:.2f}x slower than baseline")

    # ---------------- PLOTS ----------------
    plot_execution_times(results)
    plot_speedup(results)