import time
import threading
import multiprocessing

# ===============================
# Workload 
# ===============================
N = 150000


# ===============================
# CPU-bound task 
# ===============================
def heavy_task(start, end):
    total = 0
    for i in range(start, end):
        for j in range(100):
            total += i * j
    return total


# ===============================
# Sequential Execution
# ===============================
def sequential_execution(n):
    return heavy_task(0, n)


# ===============================
# Multithreading
# ===============================
def thread_worker(start, end, results, index):
    results[index] = heavy_task(start, end)


def threaded_execution(n, num_threads):
    threads = []
    results = [0] * num_threads

    step = n // num_threads

    for i in range(num_threads):
        start = i * step
        end = (i + 1) * step if i != num_threads - 1 else n

        t = threading.Thread(
            target=thread_worker,
            args=(start, end, results, i)
        )
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    return sum(results)


# ===============================
# Multiprocessing
# ===============================
def heavy_task_mp(args):
    start, end = args
    return heavy_task(start, end)


def multiprocessing_execution(n, num_processes):
    with multiprocessing.Pool(processes=num_processes) as pool:

        step = n // num_processes
        ranges = []

        for i in range(num_processes):
            start = i * step
            end = (i + 1) * step if i != num_processes - 1 else n
            ranges.append((start, end))

        results = pool.map(heavy_task_mp, ranges)

    return sum(results)


# ===============================
# Timing Function
# ===============================
def measure_time(func, *args):
    start = time.perf_counter()
    result = func(*args)
    end = time.perf_counter()
    return end - start, result


# ===============================
# Main Execution
# ===============================
if __name__ == "__main__":

    print("=" * 60)
    print("PARALLEL COMPUTING DEMONSTRATION")
    print("=" * 60)

    # Sequential
    seq_time, seq_result = measure_time(sequential_execution, N)
    print(f"\nSequential Time: {seq_time:.4f} seconds")

    results = []

    # ===============================
    # Threading Tests
    # ===============================
    print("\n--- THREADING RESULTS ---")
    for threads in [2, 4, 8]:

        t_time, t_result = measure_time(threaded_execution, N, threads)

        speedup = seq_time / t_time
        efficiency = speedup / threads

        results.append(("Threading", threads, t_time, speedup, efficiency))

        print(f"Threads={threads} | Time={t_time:.4f}s | "
              f"Speedup={speedup:.2f} | Efficiency={efficiency:.2%}")


    # ===============================
    # Multiprocessing Tests
    # ===============================
    print("\n--- MULTIPROCESSING RESULTS ---")
    for processes in [2, 4, 8]:

        p_time, p_result = measure_time(multiprocessing_execution, N, processes)

        speedup = seq_time / p_time
        efficiency = speedup / processes

        results.append(("Multiprocessing", processes, p_time, speedup, efficiency))

        print(f"Processes={processes} | Time={p_time:.4f}s | "
              f"Speedup={speedup:.2f} | Efficiency={efficiency:.2%}")


    # ===============================
    # Summary Table
    # ===============================
    print("\n" + "=" * 60)
    print("SUMMARY TABLE")
    print("=" * 60)

    print(f"{'Method':<15}{'Workers':<10}{'Time(s)':<12}{'Speedup':<12}{'Efficiency'}")
    print("-" * 60)

    for r in results:
        print(f"{r[0]:<15}{r[1]:<10}{r[2]:<12.4f}{r[3]:<12.2f}{r[4]:.2%}")