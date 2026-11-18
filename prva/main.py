import input_output
from pathlib import Path
import helper_functions as hf
import models as m
import constraints as cst

ROOT_DIR = Path(__file__).resolve().parent 
DATA_DIR = ROOT_DIR/"data"
  # whatever your helper file is called

def fitness_function(schedule, classrooms, teachers, classes):
    score = 1000
    for lecture in schedule:
        if not cst.teacher_qualified(lecture.teacher, schedule, teachers):
            score -= 10
        if not cst.classroom_free(lecture.classroom, schedule, classrooms):
            score -= 10
        if not cst.teacher_free(lecture.teacher, schedule):
            score -= 10

    missed_classes = cst.all_classes(schedule, classes)
    for missed_class in missed_classes:
        score -= 10 * missed_class

    return score


def main():
    classes = input_output.txt2dict(DATA_DIR / "classes.txt")
    classrooms = input_output.txt2dict(DATA_DIR / "classrooms.txt")
    teachers = input_output.txt2dict(DATA_DIR / "teachers.txt")

    unassigned_lectures = hf.generate_list_of_lectures(classes)
    schedule = hf.generate_random_chromosomes(unassigned_lectures, classrooms, teachers)

    pass


if __name__ == "__main__":
    main()