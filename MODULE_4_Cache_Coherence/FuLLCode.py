import multiprocessing as mp
import time

ITERATIONS = 10_000_000


# -------------------------------------------------
# 1. BASELINE (no sharing)
# -------------------------------------------------
def baseline_worker():
    x = 0
    for _ in range(ITERATIONS):
        x += 1


# -------------------------------------------------
# 2. FALSE SHARING
# -------------------------------------------------
def false_sharing_worker(arr, index):
    for _ in range(ITERATIONS):
        arr[index] += 1


# -------------------------------------------------
# 3. TRUE SHARING (with lock)
# -------------------------------------------------
def true_sharing_worker(counter, lock):
    for _ in range(ITERATIONS):
        with lock:
            counter.value += 1


# -------------------------------------------------
# RUN ALL TESTS
# -------------------------------------------------
if __name__ == "__main__":

    results = {}

    # =========================
    # BASELINE
    # =========================
    start = time.time()

    p1 = mp.Process(target=baseline_worker)
    p2 = mp.Process(target=baseline_worker)

    p1.start()
    p2.start()

    p1.join()
    p2.join()

    results["Baseline"] = time.time() - start


    # =========================
    # FALSE SHARING
    # =========================
    arr = mp.Array('i', 2)

    start = time.time()

    p1 = mp.Process(target=false_sharing_worker, args=(arr, 0))
    p2 = mp.Process(target=false_sharing_worker, args=(arr, 1))

    p1.start()
    p2.start()

    p1.join()
    p2.join()

    results["False Sharing"] = time.time() - start


    # =========================
    # FIX (Padding)
    # =========================
    arr = mp.Array('i', 64)

    start = time.time()

    p1 = mp.Process(target=false_sharing_worker, args=(arr, 0))
    p2 = mp.Process(target=false_sharing_worker, args=(arr, 32))

    p1.start()
    p2.start()

    p1.join()
    p2.join()

    results["Padded (Fixed)"] = time.time() - start


    # =========================
    # TRUE SHARING (LOCK)
    # =========================
    counter = mp.Value('i', 0)
    lock = mp.Lock()

    start = time.time()

    p1 = mp.Process(target=true_sharing_worker, args=(counter, lock))
    p2 = mp.Process(target=true_sharing_worker, args=(counter, lock))

    p1.start()
    p2.start()

    p1.join()
    p2.join()

    results["True Sharing"] = time.time() - start


    # =========================
    # FINAL RESULTS
    # =========================
    print("\n===== PERFORMANCE RESULTS =====")
    for k, v in results.items():
        print(f"{k}: {v:.4f} seconds")

    print("\nFinal Counter Value (True Sharing):", counter.value)