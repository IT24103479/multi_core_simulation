import multiprocessing
import time

#work done by each task
def baseline_task():
    x=0
    for _ in range(1000): #heavy computation
        x+=1

# Run baseline simulation
def run_baseline():
    start=time.time()

    processes = [] #array for processes

    #creat 4 processes
    for _ in range(4):
        p = multiprocessing.Process(target=baseline_task)
        processes.append(p)
        p.start()

    # wait for all processes to finish (to ensure accurate timing)
    for p in processes:
        p.join()

    end = time.time()

    print("Baseline execution time:", end-start)


# Run program
if __name__ == "__main__":
 for cores in [1,2,4,8]:
    print("Running with {} cores".format(cores))
    run_baseline()
# multiprocesssing re-imports the scripts to start new processes.
# if you dont use if __name__="__main__": the script would execute everything again, creating and infinite loop of processes