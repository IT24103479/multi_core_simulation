import time
import random
import queue
from multiprocessing import Process, Queue
import matplotlib.pyplot as plt


# -----------------------------
# 🔹 Worker Task
# -----------------------------
def worker_task(duration: float) -> None:
    time.sleep(duration)


# -----------------------------
# 🔹 Static Scheduling (Naive, but corrected for edge cases)
# -----------------------------
def static_worker(tasks, results: Queue, core_id: int) -> None:
    for _, duration in tasks:
        worker_task(duration)
    results.put(core_id)


def static_schedule(tasks, num_cores: int) -> float:
    if num_cores <= 0:
        raise ValueError("num_cores must be >= 1")

    if not tasks:
        return 0.0

    start_time = time.time()

    processes = []
    results = Queue()

    # Fix: avoid chunk_size==0 when num_cores > len(tasks)
    chunk_size = max(1, len(tasks) // num_cores)
    chunks = []

    for i in range(num_cores):
        start = i * chunk_size
        end = len(tasks) if i == num_cores - 1 else (i + 1) * chunk_size
        chunks.append(tasks[start:end])

    for i in range(num_cores):
        p = Process(target=static_worker, args=(chunks[i], results, i))
        processes.append(p)
        p.start()

    for p in processes:
        p.join()

    # Drain results (prevents queue buildup in some environments)
    for _ in range(num_cores):
        try:
            results.get_nowait()
        except queue.Empty:
            break

    return time.time() - start_time


# -----------------------------
# 🔹 Dynamic Scheduling
# -----------------------------
def dynamic_worker(task_queue: Queue, results: Queue, core_id: int, batch_size: int = 3) -> None:
    while True:
        tasks_to_do = []

        # Only catch the "queue is empty" case (don't hide real bugs)
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


def dynamic_schedule(tasks, num_cores: int) -> float:
    if num_cores <= 0:
        raise ValueError("num_cores must be >= 1")

    if not tasks:
        return 0.0

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

    for p in processes:
        p.join()

    # Drain results
    for _ in range(num_cores):
        try:
            results.get_nowait()
        except queue.Empty:
            break

    return time.time() - start_time


# -----------------------------
# 🔹 Task Generator
# -----------------------------
def generate_tasks(num_tasks: int, mode: str = "uneven"):
    tasks = []

    for i in range(num_tasks):
        if mode == "equal":
            duration = 0.05  # same for all tasks
        else:
            # Uneven workload
            if random.random() < 0.7:
                duration = random.uniform(0.05, 0.1)
            else:
                duration = random.uniform(0.1, 0.8)

        tasks.append((i, duration))

    return tasks


# -----------------------------
# 🔹 Print tasks in steps of 20 (instead of printing all)
# -----------------------------
def print_tasks_every_20(tasks) -> None:
    # prints task 1, 20th, 40th, 60th ... (1-based counting)
    for idx in range(1, len(tasks) + 1):
        if idx == 1 or idx % 20 == 0:
            task_id, duration = tasks[idx - 1]
            print(f"Task {idx} (id={task_id}) duration={duration:.4f}s")


# -----------------------------
# 🔹 Plotting (Reusable)
# -----------------------------
def plot_results(title_prefix: str, cores, times_static, times_dynamic) -> None:
    plt.figure()
    plt.plot(cores, times_static, marker="o", label="Static")
    plt.plot(cores, times_dynamic, marker="o", label="Dynamic")
    plt.xlabel("Number of Cores")
    plt.ylabel("Completion Time (s)")
    plt.title(f"{title_prefix} Workload - Completion Time vs Cores")
    plt.legend()
    plt.grid(True)
    plt.show()


# -----------------------------
# 🔹 Simulation Runner
# -----------------------------
def run_test(mode: str) -> None:
    num_tasks = 160
    cores_list = [1, 2, 4, 8]

    print(f"\n===== {mode.upper()} WORKLOAD TEST =====")

    tasks = generate_tasks(num_tasks, mode)

    print("Tasks (showing 1st and every 20th):")
    print_tasks_every_20(tasks)

    # Sequential baseline
    seq_time = static_schedule(tasks, 1)
    print("\nSequential Time:", round(seq_time, 3), "s")

    times_static = []
    times_dynamic = []

    for cores in cores_list:
        print(f"\nRunning with {cores} cores...")

        t_static = static_schedule(tasks, cores)
        t_dynamic = dynamic_schedule(tasks, cores)

        print(f"Static: {round(t_static, 3)} s | Dynamic: {round(t_dynamic, 3)} s")

        times_static.append(t_static)
        times_dynamic.append(t_dynamic)

    # Plot
    plot_results(mode.capitalize(), cores_list, times_static, times_dynamic)


# -----------------------------
# 🔹 Entry
# -----------------------------
if __name__ == "__main__":
    run_test("uneven")   # dynamic should win
    run_test("equal")    # static should win