import random
import time
import numpy as np
import pygad
import matplotlib.pyplot as plt
import input_output
from pathlib import Path
import helper_functions as hf
import constraints as cst

ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"


def main():
    classes = input_output.txt2dict(DATA_DIR / "classes.txt")
    classrooms = input_output.txt2dict(DATA_DIR / "classrooms.txt")
    teachers = input_output.txt2dict(DATA_DIR / "teachers.txt")

    unassigned_lectures = hf.generate_list_of_lectures(classes)
    classroom_names = list(classrooms.keys())
    teacher_names = list(teachers.keys())

    classroom_hours = []
    for name in classroom_names:
        classroom_hours.append(classrooms[name])

    earliest = 24
    latest = 0
    for name in classrooms:
        open_time, close_time = classrooms[name]
        if open_time < earliest:
            earliest = open_time
        if close_time > latest:
            latest = close_time

    qualified_teachers = []
    gene_space = []
    for lecture in unassigned_lectures:
        teacher_indexes = []
        for name in hf.find_qualified_teachers(lecture, teachers):
            teacher_indexes.append(teacher_names.index(name))
        qualified_teachers.append(teacher_indexes)

        gene_space.append(list(range(earliest, latest - lecture.duration + 1)))
        gene_space.append(list(range(len(classroom_names))))
        gene_space.append(teacher_indexes)

    def fitness_function(ga_instance, solution, solution_idx):
        schedule = hf.chromosome_decode(solution, unassigned_lectures,
                                        classroom_names, teacher_names)
        score = 1000
        for lecture in schedule:
            if not cst.classroom_free(lecture.classroom, schedule, classrooms):
                score -= 10
            if not cst.teacher_free(lecture.teacher, schedule):
                score -= 10
        return score

    def crossover_function(parents, offspring_size, ga_instance):
        offspring = []
        for k in range(offspring_size[0]):
            parent1 = parents[k % len(parents)]
            parent2 = parents[(k + 1) % len(parents)]
            bad1 = hf.find_conflicting_lectures(parent1, unassigned_lectures, classroom_hours)
            bad2 = hf.find_conflicting_lectures(parent2, unassigned_lectures, classroom_hours)

            child = list(parent1)
            for i in range(len(unassigned_lectures)):
                if i in bad1 and i not in bad2:
                    take_parent2 = True
                elif i in bad2 and i not in bad1:
                    take_parent2 = False
                else:
                    take_parent2 = random.random() < 0.5
                if take_parent2:
                    child[3 * i:3 * i + 3] = parent2[3 * i:3 * i + 3]
            offspring.append(child)
        return np.array(offspring)

    def mutation_function(offspring, ga_instance):
        for k in range(len(offspring)):
            if random.random() > 0.3:
                continue
            chromosome = list(offspring[k])
            bad = hf.find_conflicting_lectures(chromosome, unassigned_lectures, classroom_hours)

            if bad and random.random() < 0.8:
                i = random.choice(bad)
            else:
                i = random.randrange(len(unassigned_lectures))

            slot = hf.find_free_slot(i, chromosome, unassigned_lectures,
                                     classroom_hours, qualified_teachers)
            if slot is not None:
                chromosome[3 * i:3 * i + 3] = slot
                offspring[k] = chromosome
        return offspring

    def run_ga(improved, seed):
        random.seed(seed)
        np.random.seed(seed)

        times = {"fitness": 0, "selection": 0, "crossover": 0, "mutation": 0}
        generation_times = []
        fitness_time = [0]
        fitness_time_at_start = [None]
        clock = {"last": 0, "start": 0}

        def tick(step):
            now = time.perf_counter()
            times[step] += now - clock["last"]
            clock["last"] = now

        def timed_fitness(ga_instance, solution, solution_idx):
            start = time.perf_counter()
            result = fitness_function(ga_instance, solution, solution_idx)
            fitness_time[0] += time.perf_counter() - start
            return result

        def on_start(ga_instance):
            clock["last"] = time.perf_counter()
            clock["start"] = clock["last"]

        def on_fitness(ga_instance, population_fitness):
            if fitness_time_at_start[0] is None:
                fitness_time_at_start[0] = fitness_time[0]
            clock["last"] = time.perf_counter()

        def on_parents(ga_instance, selected_parents):
            tick("selection")

        def on_crossover(ga_instance, offspring_crossover):
            tick("crossover")

        def on_mutation(ga_instance, offspring_mutation):
            tick("mutation")

        def on_generation(ga_instance):
            now = time.perf_counter()
            if fitness_time_at_start[0] is not None:
                times["fitness"] += fitness_time[0] - fitness_time_at_start[0]
            fitness_time_at_start[0] = fitness_time[0]
            clock["last"] = now
            generation_times.append(now - clock["start"])

        settings = dict(
            num_generations=2000,
            num_parents_mating=10,
            sol_per_pop=50,
            num_genes=len(unassigned_lectures) * 3,
            gene_type=int,
            fitness_func=timed_fitness,
            random_seed=seed,
            stop_criteria="reach_1000",
            on_start=on_start,
            on_fitness=on_fitness,
            on_parents=on_parents,
            on_crossover=on_crossover,
            on_mutation=on_mutation,
            on_generation=on_generation,
        )

        init_time = 0
        if improved:
            start = time.perf_counter()
            settings["initial_population"] = hf.create_initial_population(
                50, unassigned_lectures, classroom_hours, qualified_teachers, gene_space)
            init_time = time.perf_counter() - start
            settings["crossover_type"] = crossover_function
            settings["mutation_type"] = mutation_function
            settings["parent_selection_type"] = "tournament"
            settings["K_tournament"] = 3
            settings["keep_elitism"] = 2
        else:
            settings["gene_space"] = gene_space

        ga = pygad.GA(**settings)
        ga.run()

        solution, fitness, idx = ga.best_solution()
        shifted_times = []
        for t in generation_times:
            shifted_times.append(init_time + t)

        return {"fitness": fitness,
                "generations": ga.generations_completed,
                "curve": list(ga.best_solutions_fitness),
                "times": times,
                "generation_times": shifted_times,
                "init_time": init_time,
                "solution": solution}

    baseline = []
    improved = []
    for seed in range(5):
        baseline.append(run_ga(False, seed))
        improved.append(run_ga(True, seed))

    results = {"baseline": baseline, "improved": improved}
    steps = ["fitness", "selection", "crossover", "mutation"]

    for name in results:
        runs = results[name]
        print(name)
        print("  mean best fitness:", np.mean([r["fitness"] for r in runs]))
        print("  mean generations :", np.mean([r["generations"] for r in runs]))
        print("  mean total time  :", np.mean([r["generation_times"][-1] for r in runs]))
        for step in steps:
            print("  ms/generation", step, ":",
                  np.mean([r["times"][step] / r["generations"] * 1000 for r in runs]))

    longest = max(
        len(run["curve"])
        for runs in results.values()
        for run in runs
    )
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 4.5))
    for name in results:
        runs = results[name]
        padded = []
        for r in runs:
            padded.append(r["curve"] + [r["curve"][-1]] * (longest - len(r["curve"])))
        mean_curve = np.mean(padded, axis=0)
        generations = np.arange(longest)
        line, = ax1.step(generations, mean_curve, where="post", label=name)
        ax1.scatter([0], [mean_curve[0]], color=line.get_color(), zorder=3)

        for r in runs:
            n = min(len(r["curve"]) - 1, len(r["generation_times"]))
            plot_times = [r["init_time"]] + r["generation_times"][:n]
            plot_fitness = r["curve"][:n + 1]
            ax2.step(
                plot_times,
                plot_fitness,
                where="post",
                color=line.get_color(),
                alpha=0.5,
                marker=".",
            )
        ax2.plot([], [], color=line.get_color(), marker=".", label=name)
    ax1.set_xlabel("Generation")
    ax1.set_ylabel("Best fitness")
    ax1.set_title("Fitness per generation")
    ax2.set_xlabel("Elapsed time (s)")
    ax2.set_ylabel("Best fitness")
    ax2.set_title("Fitness over time")
    ax1.legend()
    ax2.legend()
    plt.tight_layout()
    plt.savefig(ROOT_DIR / "comparison_fitness.png", dpi=150)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    width = 0.4
    for j, name in enumerate(results):
        runs = results[name]
        values = []
        for step in steps:
            values.append(np.mean([r["times"][step] / r["generations"] * 1000 for r in runs]))
        ax.bar(np.arange(len(steps)) + j * width, values, width, label=name)
    ax.set_xticks(np.arange(len(steps)) + width / 2)
    ax.set_xticklabels(steps)
    ax.set_ylabel("ms per generation")
    ax.set_title("Time per GA step")
    ax.legend()
    plt.tight_layout()
    plt.savefig(ROOT_DIR / "comparison_steps.png", dpi=150)

    best = max(improved, key=lambda r: r["fitness"])
    best_schedule = hf.chromosome_decode(best["solution"], unassigned_lectures,
                                         classroom_names, teacher_names)
    print("best fitness:", best["fitness"])
    if not cst.schedule_checker(classrooms, best_schedule, teachers):
        raise RuntimeError("The best schedule does not satisfy all constraints")
    hf.display_schedule(best_schedule, classroom_names, teacher_names)


if __name__ == "__main__":
    main()
