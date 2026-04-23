import streamlit as st

from dashboard_utils import (
	run_module1_experiments,
	run_module2_experiments,
	run_module3_experiments,
	run_module4_experiments,
	run_module5_experiments,
)


st.set_page_config(
	page_title="Multi-Core Performance Dashboard",
	page_icon="📊",
	layout="wide",
	initial_sidebar_state="expanded",
)


def render_header() -> None:
	st.title("Multi-Core Performance Research Tool")
	st.markdown(
		"""
		**A clean dashboard for experimental performance analysis in multi-core systems.**
		Use the sidebar to choose a module, run experiments, and explore execution time,
		speedup, and efficiency trends in a research-driven interface.
		"""
	)


def render_sidebar() -> str:
	st.sidebar.header("Navigation")
	selection = st.sidebar.radio(
		"Select section",
		[
			"Overview",
			"Module 1: Parallelism",
			"Module 2: Processor Scheduling",
			"Module 3: Bus & Communication",
			"Module 4: Cache Coherence",
			"Module 5: Performance Evaluation",
			"Run All Experiments",
		],
	)

	st.sidebar.markdown("---")
	st.sidebar.markdown("#### Notes")
	st.sidebar.markdown(
		"- Use `Run` actions to update the charts.\n"
		"- The system uses a mix of sequential and parallel workloads.\n"
		"- Results are captured in session state for the current page."
	)

	return selection


def render_module1() -> None:
	st.header("Module 1: Parallelism")
	st.markdown(
		"Explore the performance impact of threading and multiprocessing on a CPU-bound workload."
	)

	with st.expander("Experiment configuration", expanded=True):
		problem_size = st.number_input(
			"Problem size (N)", min_value=20_000, max_value=500_000, value=100_000, step=10_000
		)
		thread_counts = st.multiselect(
			"Thread counts",
			[2, 4, 8],
			default=[2, 4, 8],
			help="Select thread counts to compare in the performance study.",
		)
		process_counts = st.multiselect(
			"Process counts",
			[2, 4, 8],
			default=[2, 4, 8],
			help="Select process counts to compare in the performance study.",
		)

	run_button = st.button("Run Module 1 Experiments")

	if run_button or "module1_results" not in st.session_state:
		with st.spinner("Running Module 1 performance tests..."):
			results_df, base_time = run_module1_experiments(
				problem_size,
				tuple(thread_counts),
				tuple(process_counts),
			)
		st.session_state["module1_results"] = results_df
		st.session_state["module1_base_time"] = base_time

	results_df = st.session_state["module1_results"]
	base_time = st.session_state["module1_base_time"]

	best_speedup = results_df["Speedup"].max()
	best_efficiency = results_df["Efficiency"].max()

	col1, col2, col3 = st.columns(3)
	col1.metric("Baseline Sequential Time", f"{base_time:.3f}s")
	col2.metric("Best Speedup", f"{best_speedup:.2f}x")
	col3.metric("Best Efficiency", f"{best_efficiency:.2%}")

	st.subheader("Execution Time Table")
	st.dataframe(results_df.style.format({
		"Time (s)": "{:.4f}",
		"Speedup": "{:.2f}",
		"Efficiency": "{:.2%}",
	}))

	chart_df = results_df.pivot(index="Workers", columns="Method", values=["Time (s)", "Speedup", "Efficiency"])

	st.subheader("Performance Summary")
	st.markdown("**Execution time and computational scaling across worker counts.**")

	time_chart = chart_df["Time (s)"]
	speedup_chart = chart_df["Speedup"]
	efficiency_chart = chart_df["Efficiency"]

	st.line_chart(time_chart)
	st.bar_chart(speedup_chart)
	st.line_chart(efficiency_chart)


def render_module3() -> None:
	st.header("Module 3: Bus & Communication")
	st.markdown(
		"Analyze shared bus contention, controlled arbitration, throughput, and wait-time trends."
	)

	st.write(
		"This simulation compares a contended shared bus against an ordered arbitration bus across processor counts."
	)

	if st.button("Run Module 3 Experiments") or "module3_summary" not in st.session_state:
		with st.spinner("Executing bus communication experiments..."):
			contended_df, controlled_df, summary_df = run_module3_experiments()
		st.session_state["module3_contended"] = contended_df
		st.session_state["module3_controlled"] = controlled_df
		st.session_state["module3_summary"] = summary_df

	contended_df = st.session_state["module3_contended"]
	controlled_df = st.session_state["module3_controlled"]
	summary_df = st.session_state["module3_summary"]

	st.subheader("Summary Metrics")
	total_processors = int(summary_df["Processors"].max())
	top_speedup = summary_df["Speedup"].max()
	st.metric("Maximum processors tested", total_processors)
	st.metric("Maximum observed speedup", f"{top_speedup:.2f}x")

	st.subheader("Wall Time Comparison")
	st.dataframe(
		summary_df[["Scenario", "Processors", "Wall Time (s)", "Throughput"]]
		.sort_values(["Scenario", "Processors"])
		.style.format({"Wall Time (s)": "{:.4f}", "Throughput": "{:.2f}"})
	)

	st.subheader("Visual Analysis")
	chart_data = summary_df.pivot(index="Processors", columns="Scenario", values="Wall Time (s)")
	st.line_chart(chart_data)
	chart_speedup = summary_df.pivot(index="Processors", columns="Scenario", values="Speedup")
	st.bar_chart(chart_speedup)

	with st.expander("Detailed results", expanded=False):
		st.write("Contended bus results")
		st.dataframe(contended_df.style.format({
			"Wall Time (s)": "{:.4f}",
			"Wall Time Std (s)": "{:.4f}",
			"Throughput": "{:.2f}",
			"Avg Wait (s)": "{:.6f}",
			"Speedup": "{:.4f}",
			"Overhead (%)": "{:.2f}",
		}))
		st.write("Controlled bus results")
		st.dataframe(controlled_df.style.format({
			"Wall Time (s)": "{:.4f}",
			"Wall Time Std (s)": "{:.4f}",
			"Throughput": "{:.2f}",
			"Avg Wait (s)": "{:.6f}",
			"Speedup": "{:.4f}",
			"Overhead (%)": "{:.2f}",
		}))


def render_module2() -> None:
	st.header("Module 2: Processor Scheduling")
	st.markdown(
		"Run the processor scheduling workload and inspect returned metrics in tabular form."
	)

	if st.button("Run Module 2 Experiments"):
		try:
			with st.spinner("Running Module 2 experiments..."):
				module2_df, module2_stdout = run_module2_experiments()
			st.session_state["module2_results"] = module2_df
			st.session_state["module2_stdout"] = module2_stdout
			st.session_state.pop("module2_error", None)
		except Exception as exc:
			st.session_state["module2_error"] = str(exc)
			st.session_state["module2_results"] = None
			st.session_state["module2_stdout"] = ""

	module2_error = st.session_state.get("module2_error")
	module2_df = st.session_state.get("module2_results")
	module2_stdout = st.session_state.get("module2_stdout", "")

	if module2_df is None and not module2_error:
		st.info("Click **Run Module 2 Experiments** to execute this module.")
		return

	if module2_error:
		st.error(f"Module 2 could not be executed: {module2_error}")
		return

	if module2_df is None or module2_df.empty:
		st.info("Module 2 ran, but no structured results were returned.")
	else:
		st.subheader("Module 2 Results")
		st.dataframe(module2_df)
		numeric_columns = module2_df.select_dtypes(include=["number"]).columns
		if len(numeric_columns) > 0:
			st.subheader("Performance Charts")
			st.line_chart(module2_df[numeric_columns])

	if module2_stdout:
		with st.expander("Module 2 Console Output", expanded=False):
			st.code(module2_stdout)


def render_module4() -> None:
	st.header("Module 4: Cache Coherence")
	st.markdown(
		"Compare baseline, false sharing, padded sharing, and true sharing performance patterns."
	)

	if st.button("Run Module 4 Experiments") or "module4_results" not in st.session_state:
		with st.spinner("Running cache coherence experiments..."):
			module4_df = run_module4_experiments()
		st.session_state["module4_results"] = module4_df

	module4_df = st.session_state["module4_results"]

	st.subheader("Execution Time and Speedup")
	st.dataframe(
		module4_df.style.format({
			"Time (s)": "{:.4f}",
			"Speedup": "{:.2f}",
			"Relative": "{:.2f}",
		})
	)

	st.subheader("Performance Charts")
	st.bar_chart(module4_df.set_index("Scenario")["Time (s)"])
	st.bar_chart(module4_df.set_index("Scenario")["Speedup"])

	most_penalized = module4_df.sort_values("Time (s)", ascending=False).iloc[0]
	st.info(
		f"Worst-case pattern: {most_penalized['Scenario']} with {most_penalized['Time (s)']:.4f}s."
	)


def render_module5() -> None:
	st.header("Module 5: Performance Evaluation")
	st.markdown(
		"Run aggregate performance-evaluation experiments and review summarized metrics."
	)

	if st.button("Run Module 5 Experiments"):
		try:
			with st.spinner("Running Module 5 experiments..."):
				module5_df, module5_stdout = run_module5_experiments()
			st.session_state["module5_results"] = module5_df
			st.session_state["module5_stdout"] = module5_stdout
			st.session_state.pop("module5_error", None)
		except Exception as exc:
			st.session_state["module5_error"] = str(exc)
			st.session_state["module5_results"] = None
			st.session_state["module5_stdout"] = ""

	module5_error = st.session_state.get("module5_error")
	module5_df = st.session_state.get("module5_results")
	module5_stdout = st.session_state.get("module5_stdout", "")

	if module5_df is None and not module5_error:
		st.info("Click **Run Module 5 Experiments** to execute this module.")
		return

	if module5_error:
		st.error(f"Module 5 could not be executed: {module5_error}")
		return

	if module5_df is None or module5_df.empty:
		st.info("Module 5 ran, but no structured results were returned.")
	else:
		st.subheader("Module 5 Results")
		st.dataframe(module5_df)
		numeric_columns = module5_df.select_dtypes(include=["number"]).columns
		if len(numeric_columns) > 0:
			st.line_chart(module5_df[numeric_columns])

	if module5_stdout:
		with st.expander("Module 5 Console Output", expanded=False):
			st.code(module5_stdout)


def render_run_all() -> None:
	st.header("Run All Experiments")
	st.markdown(
		"Launch all configured studies from a single research panel and compare findings across modules."
	)
	if "run_all_errors" not in st.session_state:
		st.session_state["run_all_errors"] = {}

	if st.button("Run Full Benchmark Suite"):
		run_all_errors = {}
		with st.spinner("Running all experiments... this may take a few minutes."):
			try:
				m2_df, _ = run_module2_experiments()
			except Exception as exc:
				m2_df = None
				run_all_errors["Module 2"] = str(exc)
			try:
				m5_df, _ = run_module5_experiments()
			except Exception as exc:
				m5_df = None
				run_all_errors["Module 5"] = str(exc)
			try:
				m1_df, _ = run_module1_experiments()
			except Exception as exc:
				m1_df = None
				run_all_errors["Module 1"] = str(exc)
			try:
				_, _, m3_summary = run_module3_experiments()
			except Exception as exc:
				m3_summary = None
				run_all_errors["Module 3"] = str(exc)
			try:
				m4_df = run_module4_experiments()
			except Exception as exc:
				m4_df = None
				run_all_errors["Module 4"] = str(exc)
		st.session_state["run_all_m1"] = m1_df
		st.session_state["run_all_m2"] = m2_df
		st.session_state["run_all_m3"] = m3_summary
		st.session_state["run_all_m4"] = m4_df
		st.session_state["run_all_m5"] = m5_df
		st.session_state["run_all_errors"] = run_all_errors

	m1_df = st.session_state.get("run_all_m1")
	m2_df = st.session_state.get("run_all_m2")
	m3_summary = st.session_state.get("run_all_m3")
	m4_df = st.session_state.get("run_all_m4")
	m5_df = st.session_state.get("run_all_m5")
	run_all_errors = st.session_state.get("run_all_errors", {})
	run_all_results = {
		"Module 1": m1_df,
		"Module 2": m2_df,
		"Module 3": m3_summary,
		"Module 4": m4_df,
		"Module 5": m5_df,
	}

	if all(value is None for value in run_all_results.values()) and not run_all_errors:
		st.info("Click **Run Full Benchmark Suite** to execute all integrated modules.")
		return

	if m1_df is not None:
		st.subheader("Module 1 Summary")
		st.dataframe(m1_df)
	if m2_df is not None:
		st.subheader("Module 2 Summary")
		st.dataframe(m2_df)
	if m3_summary is not None:
		st.subheader("Module 3 Summary")
		st.dataframe(m3_summary)
	if m4_df is not None:
		st.subheader("Module 4 Summary")
		st.dataframe(m4_df)
	if m5_df is not None:
		st.subheader("Module 5 Summary")
		st.dataframe(m5_df)
	if run_all_errors:
		for module_name, error in run_all_errors.items():
			st.error(f"{module_name} failed during full benchmark run: {error}")


def render_overview() -> None:
	st.header("Overview")
	st.markdown(
		"This dashboard is designed to support exploratory research on multi-core performance. "
		"Each module highlights a different subsystem: computational parallelism, processor scheduling, "
		"bus contention, cache coherence, and aggregate performance evaluation."
	)
	st.markdown(
		"### Key capabilities"
		"\n- Interactive experiment execution"
		"\n- Execution time tables with speedup and efficiency analysis"
		"\n- Side-by-side comparison of architectural effects"
	)

	if "module1_results" in st.session_state:
		st.markdown("#### Latest Module 1 snapshot")
		st.dataframe(st.session_state["module1_results"].head())
	if "module2_results" in st.session_state and st.session_state["module2_results"] is not None:
		st.markdown("#### Latest Module 2 snapshot")
		st.dataframe(st.session_state["module2_results"].head())
	if "module3_summary" in st.session_state:
		st.markdown("#### Latest Module 3 snapshot")
		st.dataframe(st.session_state["module3_summary"].head())
	if "module4_results" in st.session_state:
		st.markdown("#### Latest Module 4 snapshot")
		st.dataframe(st.session_state["module4_results"].head())
	if "module5_results" in st.session_state and st.session_state["module5_results"] is not None:
		st.markdown("#### Latest Module 5 snapshot")
		st.dataframe(st.session_state["module5_results"].head())


def main() -> None:
	render_header()
	section = render_sidebar()

	if section == "Overview":
		render_overview()
	elif section == "Module 1: Parallelism":
		render_module1()
	elif section == "Module 2: Processor Scheduling":
		render_module2()
	elif section == "Module 3: Bus & Communication":
		render_module3()
	elif section == "Module 4: Cache Coherence":
		render_module4()
	elif section == "Module 5: Performance Evaluation":
		render_module5()
	elif section == "Run All Experiments":
		render_run_all()


if __name__ == "__main__":
	main()
