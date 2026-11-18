import io
from pathlib import Path
import model_helper_functions as mhf

ROOT_DIR = Path(__file__).resolve().parent 
DATA_DIR = ROOT_DIR/"data"

def fitness_function():
    pass

def main():
    classes = io.txt2dict(DATA_DIR/"classes.txt")
    classrooms = io.txt2dict(DATA_DIR/"classrooms.txt")
    teachers = io.txt2dict(DATA_DIR/"teachers.txt")

    unassigned_lectures = mhf.generate_list_of_lectures(classes)
    schedule = mhf.generate_random_chromosomes(unassigned_lectures, classrooms, teachers)

    pass


if __name__ == "__main__":
    main()