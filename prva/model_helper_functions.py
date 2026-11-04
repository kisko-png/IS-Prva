from dataclasses import dataclass

@dataclass
class Lecture:
    lecture_number: int
    class_name: str
    teacher_name: str
    start_time: int
    classroom: str
    duration: int


@dataclass
class Unassigned_Lecture:
    lecture_number: int
    class_name: str
    duration: int


def generate_list_of_lectures(classes): #generates a list of unasigend lectures
    unassigned_lectures = []
    for class_name, durations in classes.items():
        for lecture_number, duration in enumerate(durations, start=1):
            unassigned_lectures.append(
                Unassigned_Lecture(
                    class_name = class_name,
                    lecture_number = lecture_number,
                    duration = duration,
                )
            )
    return unassigned_lectures


def generate_random_chromosomes(unassigned_lectures, classrooms, teachers):  #ideja je da je [(lekciaj1),(lekcija2),...]
                                                                             # kjer je lekcija 1 = (start time z intom, soba isti indeks kot v clasroom names, teacher ista logika kot soba)
    pass

def chromosome_decode(chromosome,unassigned_lectures,classrooms_names,teachers_names):
    lectures = []
    for i in range(len(chromosome)//3):
        classroom_index = chromosome[3*i+1]
        teacher_index = chromosome[3*i+2]
        lectures.append(
            Lecture(
                lecture_number = unassigned_lectures[i].lecture_number,
                class_name = unassigned_lectures[i].class_name,
                duration = unassigned_lectures[i].duration,
                teacher_name = teachers_names[teacher_index],
                start_time = chromosome[3*i],
                classroom = classrooms_names[classroom_index],

        ))
    return lectures


def check_classroom_availability(classroom):
    pass


def check_classroom_overlap(classroom):
    pass


def check_teacher_overlap(teacher):
    pass


def check_teacher_availability(teacher):
    pass