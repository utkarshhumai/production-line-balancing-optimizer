import math
import pandas as pd
import matplotlib.pyplot as plt

# ---------------------------------
# 1. TASK DATA
# ---------------------------------

task_times = {
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

AVAILABLE_TIME = 30000
DEMAND_SCENARIOS = [350, 400, 450]


# ---------------------------------
# 2. CALCULATE POSITIONAL WEIGHTS
# ---------------------------------

def calculate_positional_weights():
    successors = {task: set() for task in task_times}

    for task, preds in predecessors.items():
        for pred in preds:
            successors[pred].add(task)

    # Find all downstream successor tasks
    for task in task_times:
        stack = list(successors[task])

        while stack:
            current = stack.pop()

            for nxt in successors[current]:
                if nxt not in successors[task]:
                    successors[task].add(nxt)
                    stack.append(nxt)

    return {
        task: task_times[task]
        + sum(task_times[s] for s in successors[task])
        for task in task_times
    }


# ---------------------------------
# 3. RPW LINE BALANCING ALGORITHM
# ---------------------------------

def balance_line(cycle_time):
    weights = calculate_positional_weights()

    remaining = set(task_times)
    assigned = set()
    stations = []

    while remaining:
        station_tasks = []
        station_load = 0

        while True:
            eligible = [
                task for task in remaining
                if all(
                    p in assigned or p in station_tasks
                    for p in predecessors[task]
                )
                and station_load + task_times[task] <= cycle_time
            ]

            if not eligible:
                break

            # Highest positional weight first
            eligible.sort(
                key=lambda task: (
                    -weights[task],
                    -task_times[task],
                    task
                )
            )

            chosen = eligible[0]
            station_tasks.append(chosen)
            station_load += task_times[chosen]
            remaining.remove(chosen)

        if not station_tasks:
            raise ValueError(
                "No task fits within cycle time. "
                "Check task times and precedence constraints."
            )

        stations.append((station_tasks, station_load))
        assigned.update(station_tasks)

    return stations


# ---------------------------------
# 4. ANALYZE DEMAND SCENARIOS
# ---------------------------------

total_work = sum(task_times.values())
allocation_results = []
summary_results = []

for demand in DEMAND_SCENARIOS:

    cycle_time = AVAILABLE_TIME / demand
    stations = balance_line(cycle_time)

    station_count = len(stations)

    efficiency = (
        total_work / (station_count * cycle_time)
    ) * 100

    total_idle = (
        station_count * cycle_time - total_work
    )

    theoretical_min = math.ceil(
        total_work / cycle_time
    )

    print("\n" + "=" * 55)
    print(f"DAILY DEMAND: {demand} units")
    print(f"Cycle Time: {cycle_time:.2f} seconds")
    print(f"Theoretical Minimum Stations: {theoretical_min}")
    print(f"Stations Assigned by RPW: {station_count}")
    print(f"Line Efficiency: {efficiency:.2f}%")
    print(f"Total Idle Time: {total_idle:.2f} seconds")
    print("-" * 55)

    for number, (tasks, load) in enumerate(
        stations, start=1
    ):
        idle = cycle_time - load
        utilization = load / cycle_time * 100

        print(
            f"WS{number}: {', '.join(tasks):25s} "
            f"Load={load:5.1f}s "
            f"Idle={idle:5.1f}s "
            f"Utilization={utilization:6.2f}%"
        )

        allocation_results.append({
            "Demand": demand,
            "Cycle_Time_sec": round(cycle_time, 2),
            "Workstation": f"WS{number}",
            "Tasks": ", ".join(tasks),
            "Workload_sec": load,
            "Idle_Time_sec": round(idle, 2),
            "Utilization_pct": round(utilization, 2)
        })

    summary_results.append({
        "Demand": demand,
        "Cycle_Time_sec": round(cycle_time, 2),
        "Total_Work_sec": total_work,
        "Theoretical_Min_Stations": theoretical_min,
        "RPW_Stations": station_count,
        "Efficiency_pct": round(efficiency, 2),
        "Total_Idle_sec": round(total_idle, 2)
    })


# ---------------------------------
# 5. EXPORT RESULTS TO CSV
# ---------------------------------

pd.DataFrame(allocation_results).to_csv(
    "station_allocations.csv", index=False
)

pd.DataFrame(summary_results).to_csv(
    "scenario_summary.csv", index=False
)

print("\nResults saved successfully:")
print("1. station_allocations.csv")
print("2. scenario_summary.csv")


# STEP 4: BOTTLENECK ANALYSIS

demand = 400
cycle_time = AVAILABLE_TIME / demand
stations = balance_line(cycle_time)

names = []
loads = []
idle = []

for i, (tasks, load) in enumerate(stations, start=1):
    names.append(f"WS{i}")
    loads.append(load)
    idle.append(cycle_time - load)

print("\n--- BOTTLENECK ANALYSIS ---")

for i in range(len(names)):
    print(
        names[i],
        "| Load:", loads[i],
        "| Idle:", round(idle[i], 2),
        "| Utilization:", round(loads[i] / cycle_time * 100, 2), "%"
    )

# Workload chart
plt.figure(figsize=(10, 5))
plt.bar(names, loads)
plt.axhline(cycle_time, linestyle="--", label="Cycle Time")
plt.title("Workstation Workload - 400 Units/Day")
plt.xlabel("Workstation")
plt.ylabel("Workload (seconds)")
plt.legend()
plt.tight_layout()
plt.savefig("workstation_workload.png")
plt.show(block=False)
plt.pause(2)
plt.close()

# Idle time chart
plt.figure(figsize=(10, 5))
plt.bar(names, idle)
plt.title("Workstation Idle Time - 400 Units/Day")
plt.xlabel("Workstation")
plt.ylabel("Idle Time (seconds)")
plt.tight_layout()
plt.savefig("workstation_idle.png")
plt.show(block=False)
plt.pause(2)
plt.close()

# STEP 5: BEFORE VS AFTER COMPARISON

total_work = sum(task_times.values())
cycle_time = AVAILABLE_TIME / 400

original_stations = 9
optimized_stations = len(balance_line(cycle_time))

original_efficiency = (
    total_work / (original_stations * cycle_time)
) * 100

optimized_efficiency = (
    total_work / (optimized_stations * cycle_time)
) * 100

original_idle = (
    original_stations * cycle_time - total_work
)

optimized_idle = (
    optimized_stations * cycle_time - total_work
)

station_reduction = (
    (original_stations - optimized_stations)
    / original_stations
) * 100

print("\n--- BEFORE VS AFTER OPTIMIZATION ---")

print("Daily demand:", 400, "units")
print("Cycle time:", cycle_time, "seconds")

print("\nBEFORE OPTIMIZATION")
print("Workstations:", original_stations)
print("Efficiency:", round(original_efficiency, 2), "%")
print("Idle time:", round(original_idle, 2), "sec/cycle")

print("\nAFTER OPTIMIZATION")
print("Workstations:", optimized_stations)
print("Efficiency:", round(optimized_efficiency, 2), "%")
print("Idle time:", round(optimized_idle, 2), "sec/cycle")

print("\nIMPROVEMENT")
print("Station reduction:", round(station_reduction, 2), "%")
print(
    "Efficiency improvement:",
    round(optimized_efficiency - original_efficiency, 2),
    "percentage points"
)
print("STEP 5 CODE EXECUTED")