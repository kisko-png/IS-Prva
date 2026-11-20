import random
from models import Lecture, UnassignedLecture

import matplotlib.pyplot as plt
from matplotlib import colormaps


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




def display_schedule(schedule, classroom_names, teacher_names, group_by="classroom"): #generated with ai
    """Draw a Gantt chart of a schedule (list of Lecture).

    group_by="classroom" -> one row per classroom (default)
    group_by="teacher"   -> one row per teacher
    """
    rows = classroom_names if group_by == "classroom" else teacher_names
    row_index = {name: i for i, name in enumerate(rows)}

    class_names = sorted({lec.class_name for lec in schedule})
    cmap = colormaps["tab20"]
    colors = {name: cmap(i % 20) for i, name in enumerate(class_names)}

    fig, ax = plt.subplots(figsize=(12, 0.9 * len(rows) + 2))

    for lec in schedule:
        if lec.start_time is None or lec.classroom is None:
            continue  # lecture could not be placed

        key = lec.classroom if group_by == "classroom" else lec.teacher
        y = row_index[key]
        other = lec.teacher if group_by == "classroom" else lec.classroom

        ax.broken_barh(
            [(lec.start_time, lec.duration)], (y - 0.4, 0.8),
            facecolors=colors[lec.class_name], edgecolor="black", alpha=0.85,
        )
        ax.text(
            lec.start_time + lec.duration / 2, y,
            f"{lec.class_name} #{lec.lecture_number}\n{other}",
            ha="center", va="center", fontsize=8,
        )

    starts = [l.start_time for l in schedule if l.start_time is not None]
    ends = [l.start_time + l.duration for l in schedule if l.start_time is not None]
    ax.set_xlim(min(starts) - 0.5, max(ends) + 0.5)
    ax.set_xticks(range(min(starts), max(ends) + 1))
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels(rows)
    ax.invert_yaxis()
    ax.set_xlabel("Hour")
    ax.set_title(f"Schedule by {group_by}")
    ax.grid(axis="x", linestyle="--", alpha=0.5)

    handles = [plt.Rectangle((0, 0), 1, 1, color=colors[n]) for n in class_names]
    ax.legend(handles, class_names, title="Class",
              bbox_to_anchor=(1.01, 1), loc="upper left")

    plt.tight_layout()
    plt.show()