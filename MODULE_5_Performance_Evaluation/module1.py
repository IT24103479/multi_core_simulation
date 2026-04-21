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

    # ===============================
    # Performance Metrics Graphs
    # ===============================
    try:
        import matplotlib.pyplot as plt
        
        workers = [2, 4, 8]
        threading_times = [r[2] for r in results if r[0] == "Threading"]
        mp_times = [r[2] for r in results if r[0] == "Multiprocessing"]
        threading_speedup = [r[3] for r in results if r[0] == "Threading"]
        mp_speedup = [r[3] for r in results if r[0] == "Multiprocessing"]
        threading_efficiency = [r[4] for r in results if r[0] == "Threading"]
        mp_efficiency = [r[4] for r in results if r[0] == "Multiprocessing"]

        # 1. Execution Time Graph
        plt.figure(figsize=(7, 5))
        plt.plot(workers, threading_times, marker='o', label='Threading')
        plt.plot(workers, mp_times, marker='s', label='Multiprocessing')
        plt.axhline(y=seq_time, color='r', linestyle='--', label='Sequential Time')
        plt.title('Execution Time')
        plt.xlabel('Number of Workers\n\nFigure 1: Execution time vs. number of workers')
        plt.ylabel('Time (s)')
        plt.xticks(workers)
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend()
        plt.tight_layout()

        # 2. Speedup Graph
        plt.figure(figsize=(7, 5))
        P_phase1 = 0.8
        amdahl_phase1 = [1 / ((1 - P_phase1) + P_phase1 / w) for w in workers]
        plt.plot(workers, threading_speedup, marker='o', label='Threading')
        plt.plot(workers, mp_speedup, marker='s', label='Multiprocessing')
        plt.plot(workers, amdahl_phase1, 'k--', label="Amdahl's Law (P=0.8)")
        plt.title('Speedup')
        plt.xlabel('Number of Workers\n\nFigure 2: Speedup vs. number of workers (with Amdahl)')
        plt.ylabel('Speedup (T_seq / T_par)')
        plt.xticks(workers)
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend()
        plt.tight_layout()

        # 3. Efficiency Graph
        plt.figure(figsize=(7, 5))
        plt.plot(workers, threading_efficiency, marker='o', label='Threading')
        plt.plot(workers, mp_efficiency, marker='s', label='Multiprocessing')
        plt.title('Efficiency')
        plt.xlabel('Number of Workers\n\nFigure 3: Efficiency vs. number of workers')
        plt.ylabel('Efficiency (Speedup / Workers)')
        plt.xticks(workers)
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend()
        plt.tight_layout()

        plt.show(block=False)
        plt.pause(0.1)

    except ImportError:
        print("\n[Notice] matplotlib is not installed. Cannot generate graphs.")

    # ===============================
    # Phase 2: Performance Monitoring with psutil
    # ===============================
    print("\n" + "=" * 60)
    print("PHASE 2: PERFORMANCE MONITORING WITH PSUTIL")
    print("=" * 60)

    try:
        import psutil
        
        def monitor_execution(func, *args):
            metrics = {'cpu': [], 'mem': []}
            keep_running = True
            
            def monitor():
                psutil.cpu_percent(interval=None) # Initialize system-wide CPU
                p = psutil.Process()
                while keep_running:
                    try:
                        metrics['cpu'].append(psutil.cpu_percent(interval=None))
                        
                        total_mem = p.memory_info().rss
                        for child in p.children(recursive=True):
                            total_mem += child.memory_info().rss
                        metrics['mem'].append(total_mem / (1024 * 1024))
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                    time.sleep(0.05)
            
            monitor_thread = threading.Thread(target=monitor)
            monitor_thread.start()
            
            start = time.perf_counter()
            func(*args)
            end = time.perf_counter()
            
            keep_running = False
            monitor_thread.join()
            
            avg_cpu = sum(metrics['cpu']) / len(metrics['cpu']) if metrics['cpu'] else 0.0
            peak_mem = max(metrics['mem']) if metrics['mem'] else 0.0
            
            return end - start, avg_cpu, peak_mem

        print("Running Phase 2 tests (this will take a moment)...")
        seq_time_2, seq_cpu, seq_mem = monitor_execution(sequential_execution, N)
        print(f"Sequential - Time: {seq_time_2:.4f}s, CPU: {seq_cpu:.2f}%, Mem: {seq_mem:.2f}MB")

        psutil_results = []
        for threads in workers:
            t_time, t_cpu, t_mem = monitor_execution(threaded_execution, N, threads)
            speedup = seq_time_2 / t_time
            efficiency = speedup / threads
            psutil_results.append(("Threading", threads, t_time, speedup, efficiency, t_cpu, t_mem))
            print(f"Threading (Workers={threads}) - Time: {t_time:.4f}s, CPU: {t_cpu:.2f}%, Mem: {t_mem:.2f}MB")
            
        for processes in workers:
            p_time, p_cpu, p_mem = monitor_execution(multiprocessing_execution, N, processes)
            speedup = seq_time_2 / p_time
            efficiency = speedup / processes
            psutil_results.append(("Multiprocessing", processes, p_time, speedup, efficiency, p_cpu, p_mem))
            print(f"Multiprocessing (Workers={processes}) - Time: {p_time:.4f}s, CPU: {p_cpu:.2f}%, Mem: {p_mem:.2f}MB")

        # Plotting Phase 2 Graphs
        t_times = [r[2] for r in psutil_results if r[0] == "Threading"]
        m_times = [r[2] for r in psutil_results if r[0] == "Multiprocessing"]
        t_speedup = [r[3] for r in psutil_results if r[0] == "Threading"]
        m_speedup = [r[3] for r in psutil_results if r[0] == "Multiprocessing"]
        t_eff = [r[4] for r in psutil_results if r[0] == "Threading"]
        m_eff = [r[4] for r in psutil_results if r[0] == "Multiprocessing"]
        t_cpu = [r[5] for r in psutil_results if r[0] == "Threading"]
        m_cpu = [r[5] for r in psutil_results if r[0] == "Multiprocessing"]
        t_mem = [r[6] for r in psutil_results if r[0] == "Threading"]
        m_mem = [r[6] for r in psutil_results if r[0] == "Multiprocessing"]

        # 4. CPU Utilisation
        plt.figure(figsize=(7, 5))
        plt.plot(workers, t_cpu, marker='o', label='Threading')
        plt.plot(workers, m_cpu, marker='s', label='Multiprocessing')
        plt.title('CPU Utilisation')
        plt.xlabel('Number of Workers\n\nFigure 4: CPU utilisation vs. number of workers')
        plt.ylabel('CPU Utilisation (%)')
        plt.xticks(workers)
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend()
        plt.tight_layout()

        # 5. Memory Usage
        plt.figure(figsize=(7, 5))
        plt.plot(workers, t_mem, marker='o', label='Threading')
        plt.plot(workers, m_mem, marker='s', label='Multiprocessing')
        plt.title('Peak Memory Usage')
        plt.xlabel('Number of Workers\n\nFigure 5: Memory usage vs. number of workers')
        plt.ylabel('Memory (MB)')
        plt.xticks(workers)
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend()
        plt.tight_layout()

        plt.show()
        
    except ImportError as e:
        print(f"\n[Notice] Failed to import module for Phase 2: {e}")