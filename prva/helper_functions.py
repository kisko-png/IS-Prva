import random
from models import Lecture, UnassignedLecture


def generate_list_of_lectures(classes):
    """Generate a list of unassigned lectures from the classes dict."""
    unassigned_lectures = []
    for class_name, durations in classes.items():
        for lecture_number, duration in enumerate(durations, start=1):
            unassigned_lectures.append(
                UnassignedLecture(
                    class_name=class_name,
                    lecture_number=lecture_number,
                    duration=duration,
                )
            )
    return unassigned_lectures


def find_qualified_teachers(lecture, teachers):
    qualified_teachers = []
    for teacher_name, classes in teachers.items():
        if lecture.class_name in classes:
            qualified_teachers.append(teacher_name)
    return qualified_teachers


def reserve_time_classroom(classroom, lecture, classrooms, used_times):
    duration = lecture.duration
    earliest_start, latest_end = classrooms[classroom]
    last_start = latest_end - duration

    result = used_times.setdefault(classroom, [])

    available_times = []
    for chosen in range(earliest_start, last_start + 1):
        free = True
        for start, end in result:
            if not (chosen >= end or chosen + duration <= start):
                free = False
        if free:
            available_times.append(chosen)

    if not available_times:
        return None

    chosen = random.choice(available_times)
    result.append((chosen, chosen + duration))
    return chosen


def generate_random_chromosomes(unassigned_lectures, classrooms, teachers):

    generated_lectures = []
    used_times = {}  # fresh bookings for every generated schedule

    for lecture in unassigned_lectures:
        qualified_teachers = find_qualified_teachers(lecture, teachers)
        if not qualified_teachers:
            raise ValueError(
                f"No teacher can teach '{lecture.class_name}' "
                "(check spelling and capitalisation in Classes.txt and Teachers.txt)"
            )
        teacher = random.choice(qualified_teachers)

        classroom_names = list(classrooms.keys())
        random.shuffle(classroom_names)

        classroom = None
        start_time = None

        for name in classroom_names:
            start_time = reserve_time_classroom(name, lecture, classrooms, used_times)

            if start_time is not None:
                classroom = name
                break

        generated_lectures.append(
            Lecture(
                lecture_number=lecture.lecture_number,
                class_name=lecture.class_name,
                duration=lecture.duration,
                teacher=teacher,
                start_time=start_time,
                classroom=classroom,
            )
        )

    return generated_lectures


def chromosome_decode(chromosome, unassigned_lectures, classrooms_names, teachers_names):
    """Turn a flat chromosome [start, classroom_idx, teacher_idx, ...] into Lectures."""
    lectures = []
    for i in range(len(chromosome) // 3):
        classroom_index = chromosome[3 * i + 1]
        teacher_index = chromosome[3 * i + 2]
        lectures.append(
            Lecture(
                lecture_number=unassigned_lectures[i].lecture_number,
                class_name=unassigned_lectures[i].class_name,
                duration=unassigned_lectures[i].duration,
                teacher=teachers_names[teacher_index],
                start_time=chromosome[3 * i],
                classroom=classrooms_names[classroom_index],
            )
        )
    return lectures


#def display_schedule(unassigned_lectures, classrooms_names, teachers_names):
