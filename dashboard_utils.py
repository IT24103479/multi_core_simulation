import contextlib
import importlib.util
import io
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Tuple

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
spec = importlib.util.spec_from_file_location("module3_bus_communication", 
                                               module3_path / "module3_bus_communication.py")
module3 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module3)
collect_results = module3.collect_results

from MODULE_4_Cache_Coherence.FuLLCode import run_tests


def _discover_python_script(module_dir: Path) -> Path:
    scripts = sorted(
        path
        for path in module_dir.glob("*.py")
        if (
            path.is_file()
            and path.name != "__init__.py"
            and not path.name.startswith(("test_", "_"))
        )
    )
    if not scripts:
        raise FileNotFoundError(
            f"No Python experiment script found in '{module_dir.name}'. "
            "Add a .py file with an experiment runner function."
        )
    if len(scripts) > 1:
        script_names = ", ".join(path.name for path in scripts)
        raise RuntimeError(
            f"Multiple experiment scripts found in '{module_dir.name}': {script_names}. "
            "Keep a single runner script in this directory for dashboard integration."
        )
    return scripts[0]


def _load_module_from_file(module_name: str, script_path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module from '{script_path}'.")
    loaded_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded_module)
    return loaded_module


def _results_to_dataframe(results: Any) -> pd.DataFrame:
    def _is_scalar_like(value: Any) -> bool:
        return (
            isinstance(value, (str, bytes, bytearray))
            or not isinstance(value, (Mapping, Sequence, np.ndarray))
        )

    if isinstance(results, pd.DataFrame):
        return results.copy()

    if isinstance(results, tuple):
        parts = []
        for index, value in enumerate(results, start=1):
            part_df = _results_to_dataframe(value)
            if not part_df.empty:
                part_df.insert(0, "Result Set", index)
                parts.append(part_df)
        return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()

    if isinstance(results, Mapping):
        if not results:
            return pd.DataFrame()
        scalar_values = all(_is_scalar_like(value) for value in results.values())
        if scalar_values:
            return pd.DataFrame([dict(results)])
        try:
            return pd.DataFrame(results)
        except ValueError:
            return (
                pd.DataFrame.from_dict(dict(results), orient="index", columns=["Value"])
                .reset_index()
                .rename(columns={"index": "Metric"})
            )

    if isinstance(results, np.ndarray):
        return pd.DataFrame(results)

    if isinstance(results, Sequence) and not isinstance(results, (str, bytes, bytearray)):
        return pd.DataFrame(list(results))

    if results is None:
        return pd.DataFrame()

    return pd.DataFrame({"Value": [results]})


def _run_generic_module_experiments(module_dir: Path, module_name: str) -> Tuple[pd.DataFrame, str]:
    """Execute a module runner script, capture stdout, and normalize outputs to a DataFrame."""

    script_path = _discover_python_script(module_dir)
    module = _load_module_from_file(f"{module_name.replace(' ', '_').lower()}_runner", script_path)
    candidate_functions = [
        "run_experiments",
        "run_tests",
        "collect_results",
        "run_simulation",
        "evaluate_performance",
        "main",
    ]
    candidate_functions.extend(
        name
        for name in dir(module)
        if (
            name.endswith("_main")
            and callable(getattr(module, name))
            and name not in candidate_functions
        )
    )

    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        results = None
        for func_name in candidate_functions:
            candidate = getattr(module, func_name, None)
            if callable(candidate):
                results = candidate()
                break

    if results is None:
        raise RuntimeError(
            f"No supported runner function found in '{script_path.name}'. "
            f"Expected one of: {', '.join(candidate_functions)}."
        )

    dataframe = _results_to_dataframe(results)
    captured_stdout = output.getvalue().strip()
    if dataframe.empty and captured_stdout:
        dataframe = pd.DataFrame({"Output": captured_stdout.splitlines()})

    return dataframe, captured_stdout


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


def run_module2_experiments() -> Tuple[pd.DataFrame, str]:
    """Run Module 2 processor-scheduling experiments and return a display DataFrame."""

    module_dir = Path(__file__).parent / "MODULE_2_Processor_Scheduling"
    return _run_generic_module_experiments(module_dir, "Module 2")


def run_module5_experiments() -> Tuple[pd.DataFrame, str]:
    """Run Module 5 performance-evaluation experiments and return a display DataFrame."""

    module_dir = Path(__file__).parent / "MODULE_5_Performance_Evaluation"
    return _run_generic_module_experiments(module_dir, "Module 5")
