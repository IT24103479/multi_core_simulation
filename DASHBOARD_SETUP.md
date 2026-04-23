# Multi-Core Performance Dashboard - Setup & Usage Guide

## Overview
This Streamlit-based dashboard provides an interactive, research-quality interface for analyzing multi-core computing performance across three major subsystems:
- **Module 1**: Parallelism (threading & multiprocessing)
- **Module 3**: Bus & Communication (contention & arbitration)
- **Module 4**: Cache Coherence (false sharing, padding, true sharing)

---

## Installation

### Prerequisites
Ensure Python 3.8+ is installed. Install the required dependencies:

```bash
pip install streamlit pandas numpy matplotlib
```

### Verify Installation
```bash
python -m py_compile app.py
python -m py_compile dashboard_utils.py
python -m py_compile MODULE_4_Cache_Coherence/FuLLCode.py
```

---

## Running the Dashboard

### Launch Streamlit App
From the project root directory:

```bash
streamlit run app.py
```

This opens the dashboard in your default web browser at `http://localhost:8501`.

---

## Dashboard Structure

### Navigation (Sidebar)
- **Overview**: Quick snapshot of latest results
- **Module 1: Parallelism**: Threading vs multiprocessing analysis
- **Module 3: Bus & Communication**: Contended vs controlled bus simulation
- **Module 4: Cache Coherence**: Cache patterns impact analysis
- **Run All Experiments**: Execute full benchmark suite at once

### Features per Section

#### Module 1: Parallelism
- **Configuration Panel**: Adjust problem size, thread/process counts
- **Metrics Cards**: Baseline time, best speedup, best efficiency
- **Execution Time Table**: Detailed timing for each configuration
- **Charts**: 
  - Line chart of execution times
  - Bar chart of speedup
  - Line chart of efficiency

#### Module 3: Bus & Communication
- **Metrics**: Total processors, maximum speedup
- **Comparison Table**: Wall time, throughput across scenarios
- **Charts**:
  - Line chart: Wall time comparison
  - Bar chart: Speedup by scenario
- **Detailed Results**: Expandable sections with full simulation metrics

#### Module 4: Cache Coherence
- **Results Table**: Time, speedup, and relative metrics
- **Charts**:
  - Bar chart: Execution time by pattern
  - Bar chart: Speedup by pattern
- **Insight Card**: Worst-case performance pattern

#### Run All Experiments
- **Single Button**: Execute all modules with default settings
- **Summary View**: Aggregated results from all three modules
- **Time**: Takes 2–5 minutes depending on system

---

## File Structure

```
multi_core_simulation/
├── app.py                           # Main Streamlit dashboard
├── dashboard_utils.py               # Shared experiment runners
├── DASHBOARD_SETUP.md               # This file
├── MODULE_1_Parallelism/
│   └── module1_parallelism.py       # Threading & multiprocessing logic
├── MODULE_3_Bus_&_Communication/
│   └── module3_bus_communication.py # Bus contention simulation
├── MODULE_4_Cache_Coherence/
│   └── FuLLCode.py                  # Cache coherence patterns
├── MODULE_2_Processor_Scheduling/   # (Not yet integrated)
├── MODULE_5_Performance_Evaluation/ # (Not yet integrated)
└── README.md                        # Project overview
```

---

## Key Design Decisions

### Modular Architecture
- `dashboard_utils.py`: Wrapper functions that clean console output (redirect stdout) and return pandas DataFrames for Streamlit display
- Each module (`1`, `3`, `4`) maintains its own simulation logic
- Plotting functions refactored to return Matplotlib figures instead of calling `plt.show()`

### Session State Management
- Results cached in `st.session_state` to preserve data when switching tabs
- Avoids re-running experiments on every navigation change
- Users can manually click "Run" buttons to refresh

### Performance Considerations
- **Module 1**: ~10–30 seconds (varies with problem size)
- **Module 3**: ~20–40 seconds (includes 3 repeats per processor count)
- **Module 4**: ~30–60 seconds (multiprocessing overhead)
- **All experiments**: ~2–5 minutes total

---

## Customization Tips

### Adjust Module 1 Workload
Edit `run_module1_experiments()` in `dashboard_utils.py`:
```python
problem_size = st.number_input(
    "Problem size (N)", 
    min_value=20_000,    # Adjust lower bound
    max_value=500_000,   # Adjust upper bound
    value=100_000,       # Default
    step=10_000
)
```

### Add New Metrics
1. Extend the relevant experiment runner function in `dashboard_utils.py`
2. Return additional columns in the pandas DataFrame
3. Display in the appropriate render function in `app.py`

### Modify Chart Styling
Update color schemes and labels in the render functions (e.g., `render_module1()`):
```python
st.bar_chart(speedup_chart)  # Streamlit auto-colors
```

---

## Troubleshooting

### Issue: "No module named 'streamlit'"
**Solution**: Install Streamlit:
```bash
pip install streamlit
```

### Issue: "MODULE_3_Bus_&_Communication" SyntaxError
**Solution**: The `&` character is handled via importlib in `dashboard_utils.py`. Ensure `dashboard_utils.py` is up-to-date.

### Issue: Experiments run very slowly
**Solution**: Reduce problem size in Module 1, or skip "Run All Experiments" and run individual modules.

### Issue: "Module 2 is taking too long"
**Solution**: Module 2 (Processor Scheduling) is currently a planned enhancement and is not integrated into `app.py` yet. The dashboard currently runs only Modules 1, 3, and 4.

### Issue: Charts not displaying
**Solution**: Ensure Matplotlib is installed:
```bash
pip install matplotlib
```

---

## Future Enhancements

- **Module 2**: Processor scheduling integration
- **Module 5**: Aggregate performance evaluation across all modules
- **Export Results**: CSV/JSON download functionality
- **Comparison Views**: Side-by-side benchmark comparisons across runs
- **Real-time Monitoring**: Live progress indicators for long-running experiments

---

## References

- **Streamlit Documentation**: https://docs.streamlit.io
- **Pandas DataFrames**: https://pandas.pydata.org/docs/
- **Matplotlib Figures**: https://matplotlib.org/stable/api/figure_api.html

---

## Author Notes

This dashboard was built as a research tool for multi-core computing analysis. The modular design allows easy extension with new simulation modules and visualizations while maintaining clean separation of concerns.

**Questions or Issues?** Review the code comments in `app.py` and `dashboard_utils.py` for detailed explanations.
