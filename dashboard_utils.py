import contextlib
import io
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

# Add MODULE_3 path to sys.path to handle the special character in folder name
module3_path = Path(__file__).parent / "MODULE_3_Bus_&_Communication"
sys.path.insert(0, str(module3_path.parent))

from MODULE_1_Parallelism.module1_parallelism import (
    measure_time,
    sequential_execution,
    threaded_execution,
    multiprocessing_execution,
)

# Import Module 3 with special handling for the folder name
import importlib.util
spec = importlib.util.spec_from_file_location("module3_bus_communication", 
                                               module3_path / "module3_bus_communication.py")
module3 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module3)
collect_results = module3.collect_results

from MODULE_4_Cache_Coherence.FuLLCode import run_tests


def run_module1_experiments(
    problem_size: int = 100_000,
    thread_counts: Tuple[int, ...] = (2, 4, 8),
    process_counts: Tuple[int, ...] = (2, 4, 8),
) -> Tuple[pd.DataFrame, float]:
    """Run the parallelism workload for sequential, threading, and multiprocessing."""

    seq_time, _ = measure_time(sequential_execution, problem_size)
    records = []

    for threads in thread_counts:
        elapsed, _ = measure_time(threaded_execution, problem_size, threads)
        speedup = seq_time / elapsed if elapsed else 0.0
        efficiency = speedup / threads if threads else 0.0
        records.append(
            {
                "Method": "Threading",
                "Workers": threads,
                "Time (s)": elapsed,
                "Speedup": speedup,
                "Efficiency": efficiency,
            }
        )

    for processes in process_counts:
        elapsed, _ = measure_time(multiprocessing_execution, problem_size, processes)
        speedup = seq_time / elapsed if elapsed else 0.0
        efficiency = speedup / processes if processes else 0.0
        records.append(
            {
                "Method": "Multiprocessing",
                "Workers": processes,
                "Time (s)": elapsed,
                "Speedup": speedup,
                "Efficiency": efficiency,
            }
        )

    df = pd.DataFrame(records)
    df["Efficiency"] = df["Efficiency"].round(4)
    return df, seq_time


def run_module3_experiments() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Run the bus simulation experiments and return DataFrames for analysis."""

    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        contended_results, controlled_results = collect_results()

    # Build contended and controlled DataFrames with Scenario column
    contended_df = pd.DataFrame(contended_results)
    contended_df["Scenario"] = "Contended"
    
    controlled_df = pd.DataFrame(controlled_results)
    controlled_df["Scenario"] = "Controlled"

    # Get baseline for speedup calculation
    baseline_time = controlled_df.loc[controlled_df["num_processors"] == 1, "wall_time"].iloc[0]
    
    # Add Speedup to both DataFrames
    contended_df["Speedup"] = baseline_time / contended_df["wall_time"]
    controlled_df["Speedup"] = baseline_time / controlled_df["wall_time"]
    
    # Add Overhead only to contended (controlled overhead is 0)
    contended_df["Overhead (%)"] = (
        (contended_df["wall_time"] - controlled_df["wall_time"].values) / 
        controlled_df["wall_time"].values
    ) * 100
    controlled_df["Overhead (%)"] = 0.0

    # Rename columns for display
    display_rename = {
        "num_processors": "Processors",
        "wall_time": "Wall Time (s)",
        "wall_time_std": "Wall Time Std (s)",
    }
    
    contended_df = contended_df.rename(columns=display_rename)
    controlled_df = controlled_df.rename(columns=display_rename)

    # Build summary DataFrame from raw lists for robustness
    summary_records = []
    for contended_result, controlled_result in zip(contended_results, controlled_results):
        speedup_contended = baseline_time / contended_result["wall_time"]
        speedup_controlled = baseline_time / controlled_result["wall_time"]
        
        summary_records.append({
            "Scenario": "Contended",
            "Processors": contended_result["num_processors"],
            "Wall Time (s)": contended_result["wall_time"],
            "Speedup": speedup_contended,
            "Throughput": contended_result["throughput"],
            "Bus Utilization": contended_result["bus_util"],
        })
        summary_records.append({
            "Scenario": "Controlled",
            "Processors": controlled_result["num_processors"],
            "Wall Time (s)": controlled_result["wall_time"],
            "Speedup": speedup_controlled,
            "Throughput": controlled_result["throughput"],
            "Bus Utilization": controlled_result["bus_util"],
        })

    summary_df = pd.DataFrame(summary_records)
    
    return contended_df, controlled_df, summary_df


def run_module4_experiments() -> pd.DataFrame:
    """Run the cache coherence patterns and return a summary DataFrame."""

    results = run_tests()
    df = pd.DataFrame.from_dict(results, orient="index", columns=["Time (s)"])
    baseline_time = df.loc["Baseline", "Time (s)"]
    df["Speedup"] = baseline_time / df["Time (s)"]
    df["Relative"] = df["Time (s)"] / baseline_time
    df = df.reset_index().rename(columns={"index": "Scenario"})
    return df
