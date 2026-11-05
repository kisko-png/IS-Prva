from dataclasses import dataclass
import random


@dataclass
class Lecture:
    lecture_number: int
    class_name: str
    teacher_name: str
    start_time: int
    classroom: str
    duration: int


@dataclass
class UnassignedLecture:
    lecture_number: int
    class_name: str
    duration: int


USED_CLASSES = {}

def generate_list_of_lectures(classes): #generates a list of unasigend lectures
    unassigned_lectures = []
    for class_name, durations in classes.items():
        for lecture_number, duration in enumerate(durations, start=1):
            unassigned_lectures.append(
                UnassignedLecture(
                    class_name = class_name,
                    lecture_number = lecture_number,
                    duration = duration,
                )
            )
    return unassigned_lectures

def find_qualified_teachers(lecture, teachers):
    qualified_teachers = []
    for teacher_name, classes in teachers.items():
        if lecture.class_name in classes:
            qualified_teachers.append(teacher_name)
    return qualified_teachers


def time_reserved_classroom(classroom):
    if classroom not in USED_CLASSES:
        return "any"
    else:
        return USED_CLASSES[classroom]


def reserve_time_classroom(classroom, lecture, classrooms):
    result = time_reserved_classroom(classroom)
    duration = lecture.duration

    earliest_start, latest_end = classrooms[classroom]
    last_start = latest_end - duration

    if last_start < earliest_start:
        return None

    if result == "any":
        USED_CLASSES[classroom] = []
        result = USED_CLASSES[classroom]

    available_times = [
        chosen for chosen in range(earliest_start, last_start + 1)
        if all(
            chosen >= end or chosen + duration <= start
            for start, end in result
        )
    ]

    if not available_times:
        return None

    chosen = random.choice(available_times)

    USED_CLASSES[classroom].append((chosen, chosen + duration))

    return chosen


def generate_random_chromosomes(unassigned_lectures, classrooms, teachers):
    generated_lectures = []

    for lecture in unassigned_lectures:
        qualified_teachers = find_qualified_teachers(lecture, teachers)
        teacher_name = random.choice(qualified_teachers)
        classroom_names = list(classrooms.keys())
        random.shuffle(classroom_names)

        classroom = None
        start_time = None

        for name in classroom_names:
            start_time = reserve_time_classroom(name, lecture, classrooms)

            if start_time is not None:
                classroom = name
                break

        randomized_lecture = Lecture(
            lecture_number=lecture.lecture_number,
            class_name=lecture.class_name,
            duration=lecture.duration,
            teacher_name=teacher_name,
            start_time=start_time,
            classroom=classroom
        )

        generated_lectures.append(randomized_lecture)

    return generated_lectures

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


def check_teacher_overlap(teacher):
    pass


def check_teacher_availability(teacher):
    pass