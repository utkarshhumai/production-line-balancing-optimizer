
import math
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="Production Line Optimizer",
    page_icon="⚙️",
    layout="wide"
)

st.title("Production Line Balancing & Capacity Optimization")
st.caption("Optimize workstation allocation using Ranked Positional Weight (RPW).")

# Task data
default_times = {
    "T1": 20, "T2": 25, "T3": 30,
    "T4": 35, "T5": 15, "T6": 40,
    "T7": 25, "T8": 30, "T9": 20,
    "T10": 35, "T11": 25, "T12": 40,
    "T13": 30, "T14": 35, "T15": 40
}

predecessors = {
    "T1": [],
    "T2": ["T1"],
    "T3": ["T1"],
    "T4": ["T2"],
    "T5": ["T2"],
    "T6": ["T3"],
    "T7": ["T4", "T5"],
    "T8": ["T6"],
    "T9": ["T7"],
    "T10": ["T7", "T8"],
    "T11": ["T9"],
    "T12": ["T10"],
    "T13": ["T11", "T12"],
    "T14": ["T13"],
    "T15": ["T14"]
}

st.sidebar.header("Production Inputs")
demand = st.sidebar.number_input(
    "Daily production demand (units)",
    min_value=1,
    value=400,
    step=10
)

available_time = st.sidebar.number_input(
    "Available production time (seconds/day)",
    min_value=1,
    value=30000,
    step=1000
)

st.sidebar.header("Task Processing Times")
task_times = {}

for task, default in default_times.items():
    task_times[task] = st.sidebar.number_input(
        f"{task} (seconds)",
        min_value=1,
        value=default,
        step=1,
        key=task
    )

cycle_time = available_time / demand
total_work = sum(task_times.values())

# Calculate RPW weights, including all downstream successors
def calculate_weights():
    successors = {task: set() for task in task_times}

    for task, preds in predecessors.items():
        for pred in preds:
            successors[pred].add(task)

    for task in task_times:
        stack = list(successors[task])

        while stack:
            current = stack.pop()

            for nxt in successors[current]:
                if nxt not in successors[task]:
                    successors[task].add(nxt)
                    stack.append(nxt)

    return {
        task: task_times[task] + sum(
            task_times[s] for s in successors[task]
        )
        for task in task_times
    }


def balance_line():
    weights = calculate_weights()
    remaining = set(task_times)
    assigned = set()
    stations = []

    while remaining:
        station_tasks = []
        load = 0

        while True:
            eligible = [
                task for task in remaining
                if all(
                    p in assigned or p in station_tasks
                    for p in predecessors[task]
                )
                and load + task_times[task] <= cycle_time
            ]

            if not eligible:
                break

            eligible.sort(
                key=lambda t: (-weights[t], -task_times[t], t)
            )

            task = eligible[0]
            station_tasks.append(task)
            load += task_times[task]
            remaining.remove(task)

        if not station_tasks:
            return None, (
                "No feasible assignment: at least one task exceeds "
                "the cycle time. Increase available time or reduce demand."
            )

        stations.append({
            "Workstation": f"WS{len(stations) + 1}",
            "Tasks": ", ".join(station_tasks),
            "Workload (sec)": load,
            "Idle (sec)": cycle_time - load,
            "Utilization (%)": load / cycle_time * 100
        })
        assigned.update(station_tasks)

    return stations, None


if cycle_time < max(task_times.values()):
    st.error(
        "Cycle time is shorter than at least one task. "
        "Adjust demand or available production time."
    )
else:
    stations, error = balance_line()

    if error:
        st.error(error)
    else:
        station_count = len(stations)
        efficiency = total_work / (station_count * cycle_time) * 100
        total_idle = station_count * cycle_time - total_work

        st.subheader("Performance Summary")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Cycle Time", f"{cycle_time:.2f} sec")
        c2.metric("Workstations", station_count)
        c3.metric("Line Efficiency", f"{efficiency:.2f}%")
        c4.metric("Idle Time / Cycle", f"{total_idle:.2f} sec")

        st.subheader("Workstation Allocation")
        df = pd.DataFrame(stations)
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.subheader("Workload by Workstation")
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.bar(df["Workstation"], df["Workload (sec)"])
        ax.axhline(
            cycle_time,
            linestyle="--",
            label=f"Cycle time: {cycle_time:.2f} sec"
        )
        ax.set_xlabel("Workstation")
        ax.set_ylabel("Workload (seconds)")
        ax.legend()
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

        st.subheader("Utilization by Workstation")
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.bar(df["Workstation"], df["Utilization (%)"])
        ax.set_xlabel("Workstation")
        ax.set_ylabel("Utilization (%)")
        ax.set_ylim(0, 110)
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

        st.download_button(
            "Download Allocation CSV",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="station_allocations.csv",
            mime="text/csv"
        )

        summary = pd.DataFrame([{
            "Demand (units/day)": demand,
            "Available Time (sec/day)": available_time,
            "Cycle Time (sec)": cycle_time,
            "Total Work Content (sec)": total_work,
            "Workstations": station_count,
            "Efficiency (%)": efficiency,
            "Idle Time (sec/cycle)": total_idle
        }])

        st.download_button(
            "Download Performance Summary",
            data=summary.to_csv(index=False).encode("utf-8"),
            file_name="performance_summary.csv",
            mime="text/csv"
        )

st.divider()
st.caption(
    "Method: Ranked Positional Weight (RPW) heuristic. "
    "Results depend on the task times and precedence constraints."
)

# STEP 8: INTERACTIVE TASK PRECEDENCE DIAGRAM

st.divider()
st.header("Task Precedence Diagram")
st.write(
    "Arrows indicate which tasks must be completed "
    "before another task can begin."
)

# Calculate the level of each task from its predecessors
levels = {}

for task in task_times:
    preds = predecessors[task]

    if not preds:
        levels[task] = 0
    else:
        levels[task] = max(levels[p] for p in preds) + 1

# Group tasks by level
level_groups = {}

for task, level in levels.items():
    level_groups.setdefault(level, []).append(task)

# Calculate positions for each task
positions = {}

for level, tasks in level_groups.items():
    count = len(tasks)

    for index, task in enumerate(tasks):
        x = level * 2.5
        y = (count - 1) / 2 - index
        positions[task] = (x, y)

# Draw the precedence network
fig, ax = plt.subplots(figsize=(15, 8))

# Draw arrows first so nodes appear over them
for task, preds in predecessors.items():
    x2, y2 = positions[task]

    for pred in preds:
        x1, y1 = positions[pred]

        ax.annotate(
            "",
            xy=(x2 - 0.45, y2),
            xytext=(x1 + 0.45, y1),
            arrowprops=dict(
                arrowstyle="->",
                linewidth=1.3,
                color="gray",
                shrinkA=3,
                shrinkB=3
            )
        )

# Draw task boxes
for task, (x, y) in positions.items():
    ax.text(
        x, y,
        f"{task}\n{task_times[task]} sec",
        ha="center",
        va="center",
        fontsize=9,
        bbox=dict(
            boxstyle="round,pad=0.5",
            facecolor="lightblue",
            edgecolor="navy"
        ),
        zorder=3
    )

ax.set_title("Task Precedence Network", fontsize=16)
ax.set_xlabel("Task sequence level")
ax.axis("off")
fig.tight_layout()

st.pyplot(fig)
plt.close(fig)

# Show the precedence relationships as a table
st.subheader("Task Precedence Details")

precedence_df = pd.DataFrame([
    {
        "Task": task,
        "Processing Time (sec)": task_times[task],
        "Immediate Predecessors": (
            ", ".join(predecessors[task])
            if predecessors[task]
            else "None"
        )
    }
    for task in task_times
])

st.dataframe(
    precedence_df,
    use_container_width=True,
    hide_index=True
)
