import random
import time
import numpy as np
import pygad
from pathlib import Path
import input_output
import helper_functions as hf
import constraints as cst
import plotting

ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"

BASE_FITNESS = 1000
HARD_WEIGHT = 20
SOFT_SCALE = 10
MULTI_HARD_WEIGHT = 10

NUM_GENERATIONS = 500
POP_SIZE = 50
NUM_PARENTS = 10
NUM_CANDIDATES = 10
MUTATION_RATE = 0.3
BAD_BIAS = 0.8
NUM_SEEDS = 3
WEIGHT_SETTINGS = [(1.0, 0.0), (0.75, 0.25), (0.5, 0.5), (0.25, 0.75), (0.0, 1.0)]


def load_problem(data_dir):
    classes = input_output.txt2dict(data_dir / "classes.txt")
    classrooms = input_output.txt2dict(data_dir / "classrooms.txt")
    teachers = input_output.txt2dict(data_dir / "teachers.txt")
    preferences = input_output.txt2dict(data_dir / "preferences.txt")

    lectures = hf.generate_list_of_lectures(classes)
    classroom_names = list(classrooms.keys())
    teacher_names = list(teachers.keys())

    classroom_hours = []
    for name in classroom_names:
        classroom_hours.append(classrooms[name])

    earliest = 24
    latest = 0
    for open_time, close_time in classroom_hours:
        earliest = min(earliest, open_time)
        latest = max(latest, close_time)

    qualified = []
    gene_space = []
    for lecture in lectures:
        teacher_indexes = []
        for name in hf.find_qualified_teachers(lecture, teachers):
            teacher_indexes.append(teacher_names.index(name))
        if not teacher_indexes:
            raise ValueError("No teacher can teach '" + lecture.class_name + "'")
        qualified.append(teacher_indexes)

        gene_space.append(list(range(earliest, latest - lecture.duration + 1)))
        gene_space.append(list(range(len(classroom_names))))
        gene_space.append(teacher_indexes)

    total_hours = 0
    for lecture in lectures:
        total_hours += lecture.duration

    return {
        "lectures": lectures,
        "classrooms": classrooms,
        "teachers": teachers,
        "classroom_names": classroom_names,
        "teacher_names": teacher_names,
        "classroom_hours": classroom_hours,
        "qualified": qualified,
        "gene_space": gene_space,
        "teacher_windows": hf.build_teacher_windows(teacher_names, preferences),
        "num_teachers": len(teacher_names),
        "target_load": total_hours / len(teacher_names),
    }


def evaluate(chromosome, problem):
    lectures = problem["lectures"]
    violations = cst.count_hard_violations(chromosome, lectures, problem["classroom_hours"])
    pref = cst.preference_score(chromosome, lectures, problem["teacher_windows"])
    loads = cst.teacher_loads(chromosome, lectures, problem["num_teachers"])
    bal = cst.balance_score(loads)
    return violations, pref, bal


def make_single_fitness(problem, w_pref, w_bal):
    def fitness_function(ga_instance, solution, solution_idx):
        violations, pref, bal = evaluate(solution, problem)
        soft = cst.soft_score(pref, bal, w_pref, w_bal)
        return BASE_FITNESS - HARD_WEIGHT * violations + SOFT_SCALE * soft
    return fitness_function


def make_multi_fitness(problem):
    def fitness_function(ga_instance, solution, solution_idx):
        violations, pref, bal = evaluate(solution, problem)
        shift = MULTI_HARD_WEIGHT * violations
        return [pref - shift, bal - shift]
    return fitness_function


def fixed_weights(w_pref, w_bal):
    def picker():
        return w_pref, w_bal
    return picker


def random_weights():
    w = random.random()
    return w, 1.0 - w


def make_crossover(problem):
    lectures = problem["lectures"]
    classroom_hours = problem["classroom_hours"]

    def crossover_function(parents, offspring_size, ga_instance):
        bad = []
        for parent in parents:
            bad.append(set(hf.find_conflicting_lectures(parent, lectures, classroom_hours)))

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


def make_mutation(problem, weight_picker):
    lectures = problem["lectures"]
    classroom_hours = problem["classroom_hours"]

    def mutation_function(offspring, ga_instance):
        for k in range(len(offspring)):
            if random.random() > MUTATION_RATE:
                continue
            chromosome = list(offspring[k])
            bad = hf.find_conflicting_lectures(chromosome, lectures, classroom_hours)

            if bad and random.random() < BAD_BIAS:
                i = random.choice(bad)
            else:
                i = random.randrange(len(lectures))

            w_pref, w_bal = weight_picker()
            slot = hf.find_better_slot(i, chromosome, problem, w_pref, w_bal, NUM_CANDIDATES)
            if slot is not None:
                chromosome[3 * i:3 * i + 3] = slot
                offspring[k] = chromosome
        return offspring
    return mutation_function


def common_settings(problem, seed, population, fitness, weight_picker, on_generation):
    return dict(
        num_generations=NUM_GENERATIONS,
        num_parents_mating=NUM_PARENTS,
        sol_per_pop=POP_SIZE,
        num_genes=len(problem["lectures"]) * 3,
        gene_type=int,
        initial_population=population,
        fitness_func=fitness,
        crossover_type=make_crossover(problem),
        mutation_type=make_mutation(problem, weight_picker),
        random_seed=seed,
        suppress_warnings=True,
        on_generation=on_generation,
    )


def run_single(problem, w_pref, w_bal, seed):
    random.seed(seed)
    np.random.seed(seed)
    start = time.perf_counter()

    picker = fixed_weights(w_pref, w_bal)
    population = hf.create_soft_population(POP_SIZE, problem, picker, NUM_CANDIDATES)
    history = []

    def on_generation(ga_instance):
        solution, fitness, index = ga_instance.best_solution(ga_instance.last_generation_fitness)
        violations, pref, bal = evaluate(solution, problem)
        if violations == 0:
            history.append(pref * bal)
        else:
            history.append(0.0)

    settings = common_settings(problem, seed, population,
                               make_single_fitness(problem, w_pref, w_bal), picker, on_generation)
    settings["parent_selection_type"] = "tournament"
    settings["K_tournament"] = 3
    settings["keep_elitism"] = 2

    ga = pygad.GA(**settings)
    ga.run()

    solution, fitness, index = ga.best_solution()
    violations, pref, bal = evaluate(solution, problem)
    points = []
    if violations == 0:
        points.append((pref, bal))

    return {
        "solution": list(solution),
        "violations": violations,
        "points": points,
        "solutions": [list(solution)] if violations == 0 else [],
        "hypervolume": hf.hypervolume_2d(points),
        "history": history,
        "time": time.perf_counter() - start,
    }


def run_multi(problem, seed):
    random.seed(seed)
    np.random.seed(seed)
    start = time.perf_counter()

    population = hf.create_soft_population(POP_SIZE, problem, random_weights, NUM_CANDIDATES)
    history = []

    def on_generation(ga_instance):
        points = []
        for row in ga_instance.last_generation_fitness:
            points.append((row[0], row[1]))
        history.append(hf.hypervolume_2d(points))

    settings = common_settings(problem, seed, population,
                               make_multi_fitness(problem), random_weights, on_generation)
    settings["parent_selection_type"] = "nsga2"
    settings["keep_elitism"] = 0

    ga = pygad.GA(**settings)
    ga.run()

    feasible_points = []
    feasible_solutions = []
    for chromosome in ga.population:
        violations, pref, bal = evaluate(chromosome, problem)
        if violations == 0:
            feasible_points.append((pref, bal))
            feasible_solutions.append(list(chromosome))

    points = []
    solutions = []
    seen = set()
    for index in hf.pareto_indexes(feasible_points):
        key = (round(feasible_points[index][0], 6), round(feasible_points[index][1], 6))
        if key in seen:
            continue
        seen.add(key)
        points.append(feasible_points[index])
        solutions.append(feasible_solutions[index])

    return {
        "violations": 0 if points else None,
        "points": points,
        "solutions": solutions,
        "hypervolume": hf.hypervolume_2d(points),
        "history": history,
        "time": time.perf_counter() - start,
    }


def describe_solution(chromosome, problem):
    violations, pref, bal = evaluate(chromosome, problem)
    loads = cst.teacher_loads(chromosome, problem["lectures"], problem["num_teachers"])
    print("hard violations (hours):", violations)
    print("preference score       :", round(pref, 3))
    print("balance score          :", round(bal, 3))
    for name, load in zip(problem["teacher_names"], loads):
        print("  ", name, load, "h")


def summarize(results):
    count = len(results)
    feasible = 0
    for result in results:
        if result["points"]:
            feasible += 1
    hypervolume = np.mean([result["hypervolume"] for result in results])
    elapsed = np.mean([result["time"] for result in results])
    return count, feasible, hypervolume, elapsed


def main():
    problem = load_problem(DATA_DIR)

    single_results = {}
    for weights in WEIGHT_SETTINGS:
        single_results[weights] = []
    multi_results = []

    for seed in range(NUM_SEEDS):
        for weights in WEIGHT_SETTINGS:
            print("seed", seed, "single fitness, weights (pref, bal) =", weights)
            single_results[weights].append(run_single(problem, weights[0], weights[1], seed))
        print("seed", seed, "multi objective (NSGA-II)")
        multi_results.append(run_multi(problem, seed))

    print()
    print("method                         feasible  mean pref  mean bal  mean HV  mean time (s)")
    for weights in WEIGHT_SETTINGS:
        results = single_results[weights]
        count, feasible, hypervolume, elapsed = summarize(results)
        pref_values = []
        bal_values = []
        for result in results:
            for pref, bal in result["points"]:
                pref_values.append(pref)
                bal_values.append(bal)
        mean_pref = np.mean(pref_values) if pref_values else float("nan")
        mean_bal = np.mean(bal_values) if bal_values else float("nan")
        name = "single w_pref=" + str(weights[0]) + " w_bal=" + str(weights[1])
        print(name.ljust(30), str(feasible) + "/" + str(count), "     ",
              round(mean_pref, 3), "    ", round(mean_bal, 3), "   ",
              round(hypervolume, 3), "  ", round(elapsed, 1))

    count, feasible, hypervolume, elapsed = summarize(multi_results)
    front_sizes = [len(result["points"]) for result in multi_results]
    print("NSGA-II".ljust(30), str(feasible) + "/" + str(count), "      -          -        ",
          round(hypervolume, 3), "  ", round(elapsed, 1))
    print("mean NSGA-II front size:", np.mean(front_sizes))

    single_points = {}
    for weights in WEIGHT_SETTINGS:
        label = "single " + str(weights)
        single_points[label] = []
        for result in single_results[weights]:
            single_points[label].extend(result["points"])
    fronts = []
    for result in multi_results:
        fronts.append(result["points"])
    plotting.plot_pareto(single_points, fronts, ROOT_DIR / "task3_pareto.png")

    histories = {}
    for weights in WEIGHT_SETTINGS:
        histories["single " + str(weights)] = [r["history"] for r in single_results[weights]]
    histories["NSGA-II"] = [r["history"] for r in multi_results]
    plotting.plot_hypervolume(histories, ROOT_DIR / "task3_hypervolume.png")

    best_run = max(multi_results, key=lambda result: result["hypervolume"])
    if best_run["points"]:
        best_index = 0
        best_value = -1.0
        for index in range(len(best_run["points"])):
            value = best_run["points"][index][0] * best_run["points"][index][1]
            if value > best_value:
                best_value = value
                best_index = index
        chosen = best_run["solutions"][best_index]
    else:
        print("NSGA-II found no feasible schedule, showing the best single run instead")
        chosen = max(single_results[(0.5, 0.5)], key=lambda result: result["hypervolume"])["solution"]

    print()
    describe_solution(chosen, problem)
    schedule = hf.chromosome_decode(chosen, problem["lectures"],
                                    problem["classroom_names"], problem["teacher_names"])
    valid = cst.schedule_checker(problem["classrooms"], schedule, problem["teachers"])
    print("schedule_checker says valid:", valid)

    hf.display_schedule(schedule, problem["classroom_names"], problem["teacher_names"], "classroom")
    hf.display_schedule(schedule, problem["classroom_names"], problem["teacher_names"], "teacher")


if __name__ == "__main__":
    main()