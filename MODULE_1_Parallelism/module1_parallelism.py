import numpy as np
import time
import threading
import multiprocessing

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


# -------------------------------
# 5. Main Execution
# -------------------------------
if __name__ == "__main__":
    print("Running Matrix Multiplication Tests...\n")

    # Sequential
    seq_time = measure_time(sequential_multiply, A, B)
    print(f"Sequential Time: {seq_time:.4f} seconds")

    results = []

    # Threading Tests
    for threads in [2, 4, 8]:
        t_time = measure_time(threaded_multiply, A, B, threads)
        speedup = seq_time / t_time
        efficiency = speedup / threads

        results.append(("Threading", threads, t_time, speedup, efficiency))
        print(f"Threading ({threads} threads): {t_time:.4f}s | Speedup: {speedup:.2f} | Efficiency: {efficiency:.2f}")

    # Multiprocessing Tests
    for processes in [2, 4, 8]:
        p_time = measure_time(multiprocessing_multiply, A, B, processes)
        speedup = seq_time / p_time
        efficiency = speedup / processes

        results.append(("Multiprocessing", processes, p_time, speedup, efficiency))
        print(f"Multiprocessing ({processes} processes): {p_time:.4f}s | Speedup: {speedup:.2f} | Efficiency: {efficiency:.2f}")

    print("\n--- Summary Table ---")
    print("Method | Workers | Time | Speedup | Efficiency")

    for r in results:
        print(f"{r[0]} | {r[1]} | {r[2]:.4f} | {r[3]:.2f} | {r[4]:.2f}")
        