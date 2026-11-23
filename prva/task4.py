import random
import sys
import time
import numpy as np
import pygad
from pathlib import Path
import input_output
import helper_functions as hf
import constraints as cst
import task3
import plotting

ROOT_DIR = Path(__file__).resolve().parent
DATA_ROOT = ROOT_DIR / "data_task4"

BASE_FITNESS = 1000
TIME_LIMIT = 20
MAX_GENERATIONS = 2000
NUM_SEEDS = 5
SWEEP_SEEDS = 3
SWEEP_TIME_LIMIT = 10

EXPERIMENTS = ["instances", "ablation", "sweeps", "failures", "task3"]

INSTANCES = {
    "small_easy": dict(rooms=6, teachers=8, keep=0.4, extra=2, seed=1),
    "small_hard": dict(rooms=6, teachers=8, keep=0.9, extra=0, seed=2),
    "medium": dict(rooms=10, teachers=14, keep=0.65, extra=1, seed=3),
    "medium_hard": dict(rooms=12, teachers=14, keep=0.95, extra=0, seed=10),
    "large_easy": dict(rooms=30, teachers=40, keep=0.5, extra=2, seed=4),
    "large_hard": dict(rooms=25, teachers=30, keep=0.95, extra=0, seed=11),
    "fail_tight": dict(rooms=20, teachers=24, keep=1.0, extra=0, seed=6),
    "fail_capacity": dict(rooms=10, teachers=14, keep=1.0, extra=1, seed=7, add_fraction=0.25),
    "fail_teacher": dict(rooms=10, teachers=14, keep=0.4, extra=2, seed=8, bottleneck=True),
}

DEFAULT_CONFIG = dict(
    init="random",
    operators="default",
    pop_size=50,
    num_parents=10,
    selection="sss",
    k_tournament=3,
    elitism=1,
    crossover="single_point",
    mutation_percent=10,
    mutation_rate=0.3,
    bad_bias=0.8,
)


def make_config(**changes):
    config = dict(DEFAULT_CONFIG)
    config.update(changes)
    return config


BASELINE = make_config()
IMPROVED = make_config(init="greedy", operators="custom", selection="tournament", elitism=2)


def plant_schedule(num_rooms, num_teachers, rng):
    windows = []
    for _ in range(num_rooms):
        windows.append([rng.choice([8, 9]), rng.choice([16, 17, 18])])

    slots = []
    for room in range(num_rooms):
        time_now = windows[room][0]
        while time_now < windows[room][1]:
            duration = min(rng.randint(1, 3), windows[room][1] - time_now)
            slots.append([room, time_now, duration, None])
            time_now += duration

    slots.sort(key=lambda slot: slot[1])
    busy_until = [0] * num_teachers
    for slot in slots:
        free = []
        for teacher in range(num_teachers):
            if busy_until[teacher] <= slot[1]:
                free.append(teacher)
        teacher = rng.choice(free)
        slot[3] = teacher
        busy_until[teacher] = slot[1] + slot[2]
    return windows, slots


def thin_out(slots, keep_fraction, rng):
    total = 0
    for slot in slots:
        total += slot[2]
    target = keep_fraction * total

    order = list(range(len(slots)))
    rng.shuffle(order)

    kept = []
    hours = 0
    for index in order:
        if hours + slots[index][2] <= target + 1e-9:
            kept.append(slots[index])
            hours += slots[index][2]
    return kept


def build_classes(slots, num_teachers, extra, rng):
    per_teacher = {}
    for slot in slots:
        per_teacher.setdefault(slot[3], []).append(slot[2])

    classes = {}
    owners = {}
    number = 1
    for teacher in sorted(per_teacher):
        durations = per_teacher[teacher]
        rng.shuffle(durations)
        position = 0
        while position < len(durations):
            size = rng.randint(2, 4)
            name = "c" + str(number).zfill(3)
            classes[name] = durations[position:position + size]
            owners[name] = teacher
            position += size
            number += 1

    qualified = {}
    for teacher in range(num_teachers):
        qualified[teacher] = []
    for name in classes:
        qualified[owners[name]].append(name)
        others = []
        for teacher in range(num_teachers):
            if teacher != owners[name]:
                others.append(teacher)
        for teacher in rng.sample(others, min(extra, len(others))):
            qualified[teacher].append(name)

    class_names = list(classes.keys())
    for teacher in range(num_teachers):
        if not qualified[teacher]:
            qualified[teacher].append(rng.choice(class_names))
    return classes, qualified


def add_classes(classes, qualified, prefix, total_hours, teacher_choices, rng):
    added = 0
    number = 1
    while added < total_hours:
        durations = []
        for _ in range(3):
            if added < total_hours:
                durations.append(2)
                added += 2
        name = prefix + str(number).zfill(2)
        classes[name] = durations
        for teacher in teacher_choices(rng):
            qualified[teacher].append(name)
        number += 1


def write_instance(folder, windows, classes, qualified, seed):
    folder.mkdir(parents=True, exist_ok=True)

    with open(folder / "classes.txt", "w", encoding="utf-8") as file:
        for name in classes:
            file.write(name + " " + str(classes[name]) + "\n")

    with open(folder / "classrooms.txt", "w", encoding="utf-8") as file:
        for index in range(len(windows)):
            file.write("R" + str(index + 1).zfill(2) + " " + str(windows[index]) + "\n")

    teacher_names = []
    with open(folder / "teachers.txt", "w", encoding="utf-8") as file:
        for teacher in range(len(qualified)):
            name = "t" + str(teacher + 1).zfill(2)
            teacher_names.append(name)
            file.write(name + " [" + ", ".join(qualified[teacher]) + "]\n")

    earliest = min(window[0] for window in windows)
    latest = max(window[1] for window in windows)
    input_output.write_random_preferences(folder / "preferences.txt", teacher_names,
                                          earliest, latest, seed)


def generate_instance(root, name, spec):
    rng = random.Random(spec["seed"])
    windows, slots = plant_schedule(spec["rooms"], spec["teachers"], rng)
    room_hours = 0
    for window in windows:
        room_hours += window[1] - window[0]

    slots = thin_out(slots, spec["keep"], rng)
    classes, qualified = build_classes(slots, spec["teachers"], spec["extra"], rng)

    if "add_fraction" in spec:
        def pick_teachers(local_rng):
            return local_rng.sample(range(spec["teachers"]), spec["extra"] + 1)
        add_classes(classes, qualified, "cx", int(spec["add_fraction"] * room_hours),
                    pick_teachers, rng)

    if spec.get("bottleneck"):
        span = max(window[1] for window in windows) - min(window[0] for window in windows)
        add_classes(classes, qualified, "cb", span + 4, lambda local_rng: [0], rng)

    write_instance(root / name, windows, classes, qualified, spec["seed"])


def generate_all(root):
    for name, spec in INSTANCES.items():
        required_files = ("classes.txt", "classrooms.txt", "teachers.txt", "preferences.txt")
        instance_dir = root / name
        if not all((instance_dir / filename).is_file() for filename in required_files):
            generate_instance(root, name, spec)


def diagnose(problem):
    lectures = problem["lectures"]
    total_hours = 0
    for lecture in lectures:
        total_hours += lecture.duration

    room_hours = 0
    earliest = 24
    latest = 0
    for open_time, close_time in problem["classroom_hours"]:
        room_hours += close_time - open_time
        earliest = min(earliest, open_time)
        latest = max(latest, close_time)
    span = latest - earliest

    forced = {}
    for index in range(len(lectures)):
        if len(problem["qualified"][index]) == 1:
            teacher = problem["qualified"][index][0]
            forced[teacher] = forced.get(teacher, 0) + lectures[index].duration

    teacher_excess = 0
    for hours in forced.values():
        teacher_excess += max(0, hours - span)
    capacity_excess = max(0, total_hours - room_hours)

    return {
        "lectures": len(lectures),
        "lecture_hours": total_hours,
        "room_hours": room_hours,
        "utilisation": total_hours / room_hours,
        "capacity_excess": capacity_excess,
        "teacher_excess": teacher_excess,
        "lower_bound": max(capacity_excess, teacher_excess),
    }


def make_hard_fitness(problem):
    lectures = problem["lectures"]
    classroom_hours = problem["classroom_hours"]

    def fitness_function(ga_instance, solution, solution_idx):
        violations = cst.count_hard_violations(solution, lectures, classroom_hours)
        return BASE_FITNESS / (1 + violations)
    return fitness_function


def make_hard_crossover(problem):
    lectures = problem["lectures"]
    classroom_hours = problem["classroom_hours"]

    def crossover_function(parents, offspring_size, ga_instance):
        bad = []
        for parent in parents:
            bad.append(set(hf.find_conflicting_lectures_fast(parent, lectures, classroom_hours)))

        offspring = []
        for k in range(offspring_size[0]):
            first = k % len(parents)
            second = (k + 1) % len(parents)

            child = list(parents[first])
            for i in range(len(lectures)):
                if i in bad[first] and i not in bad[second]:
                    take_second = True
                elif i in bad[second] and i not in bad[first]:
                    take_second = False
                else:
                    take_second = random.random() < 0.5
                if take_second:
                    child[3 * i:3 * i + 3] = parents[second][3 * i:3 * i + 3]
            offspring.append(child)
        return np.array(offspring)
    return crossover_function


def make_hard_mutation(problem, mutation_rate, bad_bias):
    lectures = problem["lectures"]
    classroom_hours = problem["classroom_hours"]
    qualified = problem["qualified"]

    def mutation_function(offspring, ga_instance):
        for k in range(len(offspring)):
            if random.random() > mutation_rate:
                continue
            chromosome = list(offspring[k])
            bad = hf.find_conflicting_lectures_fast(chromosome, lectures, classroom_hours)

            if bad and random.random() < bad_bias:
                i = random.choice(bad)
            else:
                i = random.randrange(len(lectures))

            slot = hf.find_free_slot(i, chromosome, lectures, classroom_hours, qualified)
            if slot is not None:
                chromosome[3 * i:3 * i + 3] = slot
                offspring[k] = chromosome
        return offspring
    return mutation_function


def run_hard(problem, config, seed, time_limit):
    random.seed(seed)
    np.random.seed(seed)
    start = time.perf_counter()

    population = None
    if config["init"] == "greedy":
        population = hf.create_initial_population(config["pop_size"], problem["lectures"],
                                                  problem["classroom_hours"], problem["qualified"],
                                                  problem["gene_space"])

    curve = []
    times = []

    def on_generation(ga_instance):
        # PyGAD's best_solutions_fitness history is updated at the start of
        # the next generation. Read the evaluated population here so fitness
        # and elapsed time refer to the same completed generation.
        best_fitness = float(np.max(ga_instance.last_generation_fitness))
        violations = int(round(BASE_FITNESS / best_fitness - 1))
        if curve:
            violations = min(violations, curve[-1])
        curve.append(violations)

        elapsed = time.perf_counter() - start
        times.append(elapsed)
        if elapsed >= time_limit:
            return "stop"

    settings = dict(
        num_generations=MAX_GENERATIONS,
        num_parents_mating=config["num_parents"],
        sol_per_pop=config["pop_size"],
        num_genes=len(problem["lectures"]) * 3,
        gene_type=int,
        gene_space=problem["gene_space"],
        fitness_func=make_hard_fitness(problem),
        parent_selection_type=config["selection"],
        keep_elitism=config["elitism"],
        random_seed=seed,
        suppress_warnings=True,
        stop_criteria="reach_" + str(BASE_FITNESS),
        on_generation=on_generation,
    )
    if population is not None:
        settings["initial_population"] = population
    if config["selection"] == "tournament":
        settings["K_tournament"] = config["k_tournament"]

    if config["operators"] == "custom":
        settings["crossover_type"] = make_hard_crossover(problem)
        settings["mutation_type"] = make_hard_mutation(problem, config["mutation_rate"],
                                                       config["bad_bias"])
    else:
        settings["crossover_type"] = config["crossover"]
        settings["mutation_type"] = "random"
        settings["mutation_percent_genes"] = config["mutation_percent"]

    ga = pygad.GA(**settings)
    ga.run()

    success = 0 in curve
    time_to_valid = None
    generations_to_valid = None
    if success:
        index = curve.index(0)
        time_to_valid = times[index]
        generations_to_valid = index + 1

    return {
        "success": success,
        "time_to_valid": time_to_valid,
        "generations_to_valid": generations_to_valid,
        "final_violations": curve[-1],
        "total_time": time.perf_counter() - start,
        "curve": curve,
        "times": times,
    }


def evaluate_configs(problem, configs, seeds, time_limit):
    all_results = {}
    for label, config in configs.items():
        all_results[label] = []
        for seed in range(seeds):
            all_results[label].append(run_hard(problem, config, seed, time_limit))
        print("  done:", label)
    return all_results


def summarize_hard(results):
    successes = []
    for result in results:
        if result["success"]:
            successes.append(result)

    summary = {"rate": len(successes) / len(results)}
    summary["time"] = np.mean([r["time_to_valid"] for r in successes]) if successes else float("nan")
    summary["generations"] = np.mean([r["generations_to_valid"] for r in successes]) if successes else float("nan")
    summary["violations"] = np.mean([r["final_violations"] for r in results])
    summary["total_time"] = np.mean([r["total_time"] for r in results])
    return summary


def print_hard_table(title, all_results):
    print()
    print(title)
    print("config".ljust(28), "valid runs  time to valid (s)  gens to valid  final violations  run time (s)")
    for label, results in all_results.items():
        summary = summarize_hard(results)
        print(label.ljust(28),
              (str(int(round(summary["rate"] * len(results)))) + "/" + str(len(results))).ljust(11),
              str(round(summary["time"], 2)).ljust(17),
              str(round(summary["generations"], 1)).ljust(14),
              str(round(summary["violations"], 2)).ljust(17),
              round(summary["total_time"], 1))


def curves_of(results, use_time):
    runs = []
    for result in results:
        if use_time:
            runs.append((np.array(result["times"]), np.array(result["curve"])))
        else:
            # The first value is recorded after generation 1 has completed.
            runs.append((np.arange(1, len(result["curve"]) + 1), np.array(result["curve"])))
    return runs


def bar_panel(all_results):
    labels = list(all_results.keys())
    values = []
    notes = []
    for label in labels:
        summary = summarize_hard(all_results[label])
        values.append(summary["violations"])
        notes.append(str(int(round(summary["rate"] * len(all_results[label])))) + "/" +
                     str(len(all_results[label])))
    return labels, values, notes


def load_instance(name):
    return task3.load_problem(DATA_ROOT / name)


def experiment_instances():
    names = ["small_easy", "small_hard", "medium", "medium_hard", "large_easy", "large_hard"]
    generation_panels = {}
    time_panels = {}

    for name in names:
        problem = load_instance(name)
        info = diagnose(problem)
        print()
        print(name, "lectures:", info["lectures"], "utilisation:", round(info["utilisation"], 2))
        results = evaluate_configs(problem, {"baseline (Task 1)": BASELINE,
                                             "improved (Task 2)": IMPROVED}, NUM_SEEDS, TIME_LIMIT)
        print_hard_table(name, results)

        title = name + " (" + str(info["lectures"]) + " lectures, utilisation " + \
            str(round(info["utilisation"], 2)) + ")"
        generation_panels[title] = {}
        time_panels[title] = {}
        for label, runs in results.items():
            generation_panels[title][label] = curves_of(runs, False)
            time_panels[title][label] = curves_of(runs, True)

    plotting.plot_curve_panels(generation_panels, "Completed generation", "Hard-constraint penalty units (mean)",
                               ROOT_DIR / "task4_instances_generations.png")
    plotting.plot_curve_panels(time_panels, "Elapsed time (s)", "Hard-constraint penalty units (mean)",
                               ROOT_DIR / "task4_instances_time.png", use_time=True)


def experiment_ablation(name):
    problem = load_instance(name)
    configs = {
        "baseline": BASELINE,
        "greedy init only": make_config(init="greedy"),
        "custom operators only": make_config(operators="custom"),
        "greedy + custom": make_config(init="greedy", operators="custom"),
        "improved (Task 2)": IMPROVED,
    }
    print()
    print("ablation on", name)
    results = evaluate_configs(problem, configs, NUM_SEEDS, TIME_LIMIT)
    print_hard_table("ablation on " + name, results)

    time_panels = {"ablation on " + name: {}}
    for label, runs in results.items():
        time_panels["ablation on " + name][label] = curves_of(runs, True)
    plotting.plot_curve_panels(time_panels, "Elapsed time (s)", "Hard-constraint penalty units (mean)",
                               ROOT_DIR / "task4_ablation.png", use_time=True)


def experiment_sweeps(baseline_name, improved_name):

    baseline_groups = {
        "population size": {str(v): make_config(pop_size=v) for v in [20, 50, 100]},
        "mutation percent of genes": {str(v): make_config(mutation_percent=v) for v in [5, 10, 30]},
        "crossover type": {v: make_config(crossover=v) for v in ["single_point", "two_points", "uniform"]},
        "parent selection": {v: make_config(selection=v) for v in ["sss", "tournament", "rws", "rank"]},
        "parents mating": {str(v): make_config(num_parents=v) for v in [5, 10, 25]},
    }
    improved_groups = {
        "improved: mutation rate": {str(v): make_config(init="greedy", operators="custom",
                                                          selection="tournament", elitism=2,
                                                          mutation_rate=v) for v in [0.1, 0.3, 0.6]},
        "improved: tournament size": {str(v): make_config(init="greedy", operators="custom",
                                                            selection="tournament", elitism=2,
                                                            k_tournament=v) for v in [2, 3, 6]},
        "improved: elitism": {str(v): make_config(init="greedy", operators="custom",
                                                    selection="tournament", elitism=v) for v in [0, 2, 5]},
    }

    panels = {}
    for groups, name in ((baseline_groups, baseline_name), (improved_groups, improved_name)):
        problem = load_instance(name)
        for group_name, configs in groups.items():
            print()
            print("sweep:", group_name, "on", name)
            results = evaluate_configs(problem, configs, SWEEP_SEEDS, SWEEP_TIME_LIMIT)
            print_hard_table(group_name + " on " + name, results)
            panels[group_name + " (" + name + ")"] = bar_panel(results)

    plotting.plot_bar_panels(panels, "Mean final hard-constraint penalty units (label = valid runs)",
                             ROOT_DIR / "task4_sweeps.png")


def experiment_failures():
    names = ["fail_tight", "fail_capacity", "fail_teacher"]
    time_panels = {}

    for name in names:
        problem = load_instance(name)
        info = diagnose(problem)
        print()
        print(name)
        print("  lectures:", info["lectures"], "lecture hours:", info["lecture_hours"],
              "room hours:", info["room_hours"], "utilisation:", round(info["utilisation"], 2))
        print("  capacity excess:", info["capacity_excess"], "teacher excess:", info["teacher_excess"],
              "lower bound on violated hours:", info["lower_bound"])

        results = evaluate_configs(problem, {"baseline (Task 1)": BASELINE,
                                             "improved (Task 2)": IMPROVED}, 3, TIME_LIMIT)
        print_hard_table(name, results)

        time_panels[name] = {}
        for label, runs in results.items():
            time_panels[name][label] = curves_of(runs, True)

    plotting.plot_curve_panels(time_panels, "Elapsed time (s)", "Hard-constraint penalty units (mean)",
                               ROOT_DIR / "task4_failures.png", use_time=True)


def experiment_task3(names, generations, seeds):
    task3.NUM_GENERATIONS = generations
    for name in names:
        problem = load_instance(name)
        print()
        print("Task 3 on", name, "generations:", generations)

        single_results = []
        multi_results = []
        for seed in range(seeds):
            single_results.append(task3.run_single(problem, 0.5, 0.5, seed))
            multi_results.append(task3.run_multi(problem, seed))
            print("  seed", seed, "done")

        for label, results in (("single 0.5/0.5", single_results), ("NSGA-II", multi_results)):
            count, feasible, hypervolume, elapsed = task3.summarize(results)
            print(label.ljust(16), "valid:", str(feasible) + "/" + str(count),
                  "mean HV:", round(hypervolume, 3), "mean time (s):", round(elapsed, 1))
        print("mean NSGA-II front size:", np.mean([len(r["points"]) for r in multi_results]))

        single_points = {"single 0.5/0.5": []}
        for result in single_results:
            single_points["single 0.5/0.5"].extend(result["points"])
        fronts = []
        for result in multi_results:
            fronts.append(result["points"])
        plotting.plot_pareto(single_points, fronts, ROOT_DIR / ("task4_task3_pareto_" + name + ".png"))
        plotting.plot_hypervolume({"single 0.5/0.5": [r["history"] for r in single_results],
                                   "NSGA-II": [r["history"] for r in multi_results]},
                                  ROOT_DIR / ("task4_task3_hypervolume_" + name + ".png"))


def main():
    generate_all(DATA_ROOT)
    selected = sys.argv[1:]
    if not selected:
        selected = EXPERIMENTS

    if "instances" in selected:
        experiment_instances()
    if "ablation" in selected:
        experiment_ablation("medium_hard")
    if "sweeps" in selected:
        experiment_sweeps("medium", "medium_hard")
    if "failures" in selected:
        experiment_failures()
    if "task3" in selected:
        experiment_task3(["medium", "large_easy"], 200, 3)


if __name__ == "__main__":
    main()
