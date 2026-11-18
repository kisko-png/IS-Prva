import pygad
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

    earliest = 24
    latest = 0
    for name in classrooms:
        open_time, close_time = classrooms[name]
        if open_time < earliest:
            earliest = open_time
        if close_time > latest:
            latest = close_time

    gene_space = []
    for lecture in unassigned_lectures:
        teacher_indexes = []
        for name in hf.find_qualified_teachers(lecture, teachers):
            teacher_indexes.append(teacher_names.index(name))

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

    ga = pygad.GA(
        num_generations=2000,
        num_parents_mating=10,
        sol_per_pop=50,
        num_genes=len(unassigned_lectures) * 3,
        gene_space=gene_space,
        gene_type=int,
        fitness_func=fitness_function,
    )
    ga.run()



    solution, fitness, idx = ga.best_solution()
    best_schedule = hf.chromosome_decode(solution, unassigned_lectures,
                                         classroom_names, teacher_names)
    print("best fitness:", fitness)
    for lecture in best_schedule:
        print(lecture)


if __name__ == "__main__":
    main()