# Parallel Computing Demonstration Application

## Design and Performance Analysis of Parallel Processing and Multiprocessor Architectures

![Python](https://img.shields.io/badge/Python-3.x-blue)
![Domain](https://img.shields.io/badge/Domain-Computer%20Architecture-green)
![Project Type](https://img.shields.io/badge/Project-Research%20%26%20Simulation-orange)

## Overview

This project is a **Parallel Computing Demonstration Application** developed to explore and evaluate key concepts in **parallel processing and multiprocessor architectures**.

The application provides practical implementations of parallel computing techniques, processor scheduling strategies, bus communication models, cache coherence mechanisms, and performance evaluation methods.

The project demonstrates how architectural decisions and optimization techniques influence execution time, scalability, processor utilization, and overall system performance.

**Associated with:** SLIIT  
**Module:** IE2064 – Advanced Computer Organization & Computer Architecture  
**Duration:** March 2026 – April 2026

---

# Implemented Modules

## Module 1 – Parallelism Module

This module demonstrates the performance difference between sequential and parallel execution of computationally intensive tasks.

### Implementations

- Sequential execution
- Multithreading approach
- Multiprocessing approach

### Evaluations

Execution time is measured using different configurations:

- 1 thread/process
- 2 threads/processes
- 4 threads/processes
- 8 threads/processes

### Metrics

- Execution time
- Speedup
- Efficiency

The module analyzes the performance differences between multithreading and multiprocessing approaches considering factors such as Python GIL limitations, process overhead, and parallel workload distribution.

---

# Module 2 – Processor Scheduling Module

This module simulates task distribution and scheduling across multiple processors.

### Implemented Scheduling Strategies

### Static Load Balancing

- Tasks are divided among processors before execution.
- Suitable for workloads with predictable execution times.

### Dynamic Load Balancing

- Tasks are assigned dynamically as processors become available.
- Improves performance for uneven workloads.

### Performance Analysis

The module compares:

- Task completion time
- Processor utilization
- Scheduling efficiency

under different workload conditions.

---

# Module 3 – Bus & Communication Module

This module models a shared communication bus where multiple processors compete for access.

### Implemented Features

- Multiple simulated processors accessing a shared bus
- Synchronization using locking/semaphore mechanisms
- Bus contention simulation
- Contention control mechanisms

### Analysis

The module evaluates:

- Bus transfer time
- Effect of increasing processor count
- Impact of arbitration delays and backoff mechanisms

Configurations tested:

- 1 processor
- 2 processors
- 4 processors
- 8 processors

---

# Module 4 – Cache Coherence Module

This module demonstrates cache coherence problems in multiprocessor systems.

### Implemented Scenarios

## True Sharing

Multiple processors access the same memory location, requiring synchronization between caches.

## False Sharing

Multiple processors modify different variables located within the same cache line, causing unnecessary cache invalidations.

## Cache-Aligned Baseline

Uses memory alignment techniques to reduce coherence overhead.

### Concepts Demonstrated

- MESI cache coherence protocol
- Cache state transitions
- Cache invalidation overhead
- Performance impact of sharing patterns

### Performance Metrics

- Execution time comparison
- Coherence overhead analysis
- Impact of cache-line alignment

---

# Module 5 – Performance Evaluation Module

This module collects and visualizes performance measurements from all implemented modules.

## Evaluated Metrics

- Execution time
- Speedup

$$
Speedup = \frac{T_{Sequential}}{T_{Parallel}}
$$

- Efficiency

$$
Efficiency = \frac{Speedup}{Number\ of\ Processors}
$$

- CPU utilization (%)
- Memory usage (MB)

---

# Visualization & Analysis

The application generates performance graphs including:

- Execution Time vs Number of Threads/Processes
- Speedup vs Number of Threads/Processes
- Efficiency vs Number of Threads/Processes
- CPU Utilization vs Number of Threads/Processes
- Comparison with Amdahl's Law predictions

The results are analyzed to understand:

- Parallel performance limitations
- Processing overhead
- Scheduling effects
- Memory access bottlenecks
- Scalability challenges

---

# System Integration

All five modules are integrated into a unified application with a menu-driven interface.

Users can independently execute:

1. Parallelism Simulation
2. Processor Scheduling Simulation
3. Bus Communication Simulation
4. Cache Coherence Simulation
5. Performance Evaluation

---

# Technologies Used

- Python
- multiprocessing
- threading
- NumPy
- Matplotlib
- psutil
- Time measurement utilities

---

---

# Learning Outcomes

Through this project, the following concepts were practically explored:

- Parallel programming techniques
- Multithreading and multiprocessing
- Processor scheduling algorithms
- Shared memory communication
- Cache coherence protocols
- Performance optimization techniques
- Scalability analysis in multiprocessor systems

---

# Contributors
- IT24200368 - K.A.D.S.Kasthuri 
- IT24610806 - R.A.T.P.Obeysekara 
- IT24103478 Withanage M.P.A 
- IT24101346-K.T.W.Gunasekara

Developed as a team project for:

**IE2064 – Advanced Computer Organization & Computer Architecture**  
**BSc (Hons) Information Technology – Computer Systems Engineering**  
**SLIIT**
