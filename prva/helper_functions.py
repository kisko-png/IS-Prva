import random
from models import Lecture, UnassignedLecture
import constraints as cst

import matplotlib.pyplot as plt
from matplotlib import colormaps


def generate_list_of_lectures(classes):
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


def chromosome_decode(chromosome, unassigned_lectures, classrooms_names, teachers_names):
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


def display_schedule(schedule, classroom_names, teacher_names, group_by="classroom"):
    if group_by not in ("classroom", "teacher"):
        raise ValueError("group_by must be 'classroom' or 'teacher'")

    rows = classroom_names if group_by == "classroom" else teacher_names
    row_index = {name: i for i, name in enumerate(rows)}

    class_names = sorted({lec.class_name for lec in schedule})
    cmap = colormaps["tab20"]
    colors = {name: cmap(i % 20) for i, name in enumerate(class_names)}

    fig, ax = plt.subplots(figsize=(12, 0.9 * len(rows) + 2))

    for lec in schedule:
        if lec.start_time is None or lec.classroom is None:
            continue

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

    starts = [lec.start_time for lec in schedule if lec.start_time is not None]
    ends = [
        lec.start_time + lec.duration
        for lec in schedule
        if lec.start_time is not None
    ]
    if starts:
        ax.set_xlim(min(starts) - 0.5, max(ends) + 0.5)
        ax.set_xticks(range(min(starts), max(ends) + 1))
    else:
        ax.set_xlim(0, 1)
        ax.text(0.5, 0.5, "No lectures scheduled", ha="center", va="center")

    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels(rows)
    ax.invert_yaxis()
    ax.set_xlabel("Hour")
    ax.set_title(f"Schedule by {group_by}")
    ax.grid(axis="x", linestyle="--", alpha=0.5)

    if class_names:
        handles = [
            plt.Rectangle((0, 0), 1, 1, color=colors[name])
            for name in class_names
        ]
        ax.legend(
            handles,
            class_names,
            title="Class",
            bbox_to_anchor=(1.01, 1),
            loc="upper left",
        )

    plt.tight_layout()
    plt.show()


def is_free(start, duration, booked):
    for booked_start, booked_end in booked:
        if start < booked_end and booked_start < start + duration:
            return False
    return True


def find_conflicting_lectures(chromosome, unassigned_lectures, classroom_hours):
    bad_lectures = []
    for i in range(len(unassigned_lectures)):
        start = chromosome[3 * i]
        end = start + unassigned_lectures[i].duration
        classroom = chromosome[3 * i + 1]
        teacher = chromosome[3 * i + 2]

        open_time, close_time = classroom_hours[classroom]
        bad = start < open_time or end > close_time

        for j in range(len(unassigned_lectures)):
            if j == i:
                continue
            other_start = chromosome[3 * j]
            other_end = other_start + unassigned_lectures[j].duration
            overlap = start < other_end and other_start < end
            if overlap and (chromosome[3 * j + 1] == classroom or chromosome[3 * j + 2] == teacher):
                bad = True

        if bad:
            bad_lectures.append(i)
    return bad_lectures


def find_conflicting_lectures_fast(chromosome, unassigned_lectures, classroom_hours):
    bad = set()
    classroom_groups = {}
    teacher_groups = {}

    for i in range(len(unassigned_lectures)):
        start = chromosome[3 * i]
        end = start + unassigned_lectures[i].duration
        classroom = chromosome[3 * i + 1]
        teacher = chromosome[3 * i + 2]

        open_time, close_time = classroom_hours[classroom]
        if start < open_time or end > close_time:
            bad.add(i)

        classroom_groups.setdefault(classroom, []).append((start, end, i))
        teacher_groups.setdefault(teacher, []).append((start, end, i))

    for groups in (classroom_groups, teacher_groups):
        for intervals in groups.values():
            intervals.sort()
            for a in range(len(intervals)):
                for b in range(a + 1, len(intervals)):
                    if intervals[b][0] >= intervals[a][1]:
                        break
                    bad.add(intervals[a][2])
                    bad.add(intervals[b][2])
    return sorted(bad)


def search_free_slot(duration, teacher_indexes, classroom_hours, classroom_booked, teacher_booked):
    classroom_order = list(range(len(classroom_hours)))
    random.shuffle(classroom_order)
    teacher_order = list(teacher_indexes)
    random.shuffle(teacher_order)

    for classroom in classroom_order:
        open_time, close_time = classroom_hours[classroom]
        starts = list(range(open_time, close_time - duration + 1))
        random.shuffle(starts)
        for start in starts:
            if not is_free(start, duration, classroom_booked.get(classroom, [])):
                continue
            for teacher in teacher_order:
                if is_free(start, duration, teacher_booked.get(teacher, [])):
                    return [start, classroom, teacher]
    return None


def find_free_slot(lecture_index, chromosome, unassigned_lectures, classroom_hours, qualified_teachers):
    classroom_booked = {}
    teacher_booked = {}
    for j in range(len(unassigned_lectures)):
        if j == lecture_index:
            continue
        start = chromosome[3 * j]
        end = start + unassigned_lectures[j].duration
        classroom_booked.setdefault(chromosome[3 * j + 1], []).append((start, end))
        teacher_booked.setdefault(chromosome[3 * j + 2], []).append((start, end))

    duration = unassigned_lectures[lecture_index].duration
    return search_free_slot(duration, qualified_teachers[lecture_index],
                            classroom_hours, classroom_booked, teacher_booked)


def create_greedy_chromosome(unassigned_lectures, classroom_hours, qualified_teachers, gene_space):
    num_lectures = len(unassigned_lectures)
    chromosome = [0] * (3 * num_lectures)
    classroom_booked = {}
    teacher_booked = {}

    order = list(range(num_lectures))
    random.shuffle(order)

    for i in order:
        duration = unassigned_lectures[i].duration
        slot = search_free_slot(duration, qualified_teachers[i], classroom_hours,
                                classroom_booked, teacher_booked)
        if slot is None:
            slot = [random.choice(gene_space[3 * i]),
                    random.choice(gene_space[3 * i + 1]),
                    random.choice(gene_space[3 * i + 2])]

        chromosome[3 * i:3 * i + 3] = slot
        end = slot[0] + duration
        classroom_booked.setdefault(slot[1], []).append((slot[0], end))
        teacher_booked.setdefault(slot[2], []).append((slot[0], end))
    return chromosome


def create_initial_population(size, unassigned_lectures, classroom_hours, qualified_teachers, gene_space):
    population = []
    for _ in range(size):
        population.append(create_greedy_chromosome(unassigned_lectures, classroom_hours,
                                                   qualified_teachers, gene_space))
    return population


def build_teacher_windows(teacher_names, preferences):
    windows = []
    for name in teacher_names:
        prefs = preferences.get(name, {})
        windows.append((prefs.get("likes"), prefs.get("dislikes")))
    return windows


def candidate_score(start, duration, teacher, problem, teacher_load, w_pref, w_bal):
    likes, dislikes = problem["teacher_windows"][teacher]
    net = 0
    if likes is not None:
        net += cst.overlap(start, start + duration, likes[0], likes[1])
    if dislikes is not None:
        net -= cst.overlap(start, start + duration, dislikes[0], dislikes[1])
    pref_part = net / duration

    target = problem["target_load"]
    load_part = 0.0
    if target > 0:
        load_part = (target - teacher_load[teacher]) / target
    load_part = max(-1.0, min(1.0, load_part))

    return w_pref * pref_part + w_bal * load_part


def pick_best_slot(duration, teacher_indexes, problem, classroom_booked, teacher_booked,
                   teacher_load, w_pref, w_bal, num_candidates):
    classroom_hours = problem["classroom_hours"]

    room_slots = []
    for classroom in range(len(classroom_hours)):
        open_time, close_time = classroom_hours[classroom]
        for start in range(open_time, close_time - duration + 1):
            if is_free(start, duration, classroom_booked.get(classroom, [])):
                room_slots.append((start, classroom))

    random.shuffle(room_slots)

    best = None
    best_score = None
    tried = 0
    for start, classroom in room_slots:
        free_teachers = []
        for teacher in teacher_indexes:
            if is_free(start, duration, teacher_booked.get(teacher, [])):
                free_teachers.append(teacher)
        if not free_teachers:
            continue

        for teacher in free_teachers:
            score = candidate_score(start, duration, teacher, problem, teacher_load, w_pref, w_bal)
            if best is None or score > best_score:
                best = [start, classroom, teacher]
                best_score = score

        tried += 1
        if tried >= num_candidates:
            break
    return best


def find_better_slot(lecture_index, chromosome, problem, w_pref, w_bal, num_candidates):
    lectures = problem["lectures"]
    classroom_booked = {}
    teacher_booked = {}
    teacher_load = [0] * problem["num_teachers"]

    for j in range(len(lectures)):
        if j == lecture_index:
            continue
        start = chromosome[3 * j]
        end = start + lectures[j].duration
        classroom_booked.setdefault(chromosome[3 * j + 1], []).append((start, end))
        teacher_booked.setdefault(chromosome[3 * j + 2], []).append((start, end))
        teacher_load[chromosome[3 * j + 2]] += lectures[j].duration

    return pick_best_slot(lectures[lecture_index].duration, problem["qualified"][lecture_index],
                          problem, classroom_booked, teacher_booked, teacher_load,
                          w_pref, w_bal, num_candidates)


def create_soft_chromosome(problem, w_pref, w_bal, num_candidates):
    lectures = problem["lectures"]
    gene_space = problem["gene_space"]
    num_lectures = len(lectures)
    chromosome = [0] * (3 * num_lectures)
    classroom_booked = {}
    teacher_booked = {}
    teacher_load = [0] * problem["num_teachers"]

    order = list(range(num_lectures))
    random.shuffle(order)

    for i in order:
        duration = lectures[i].duration
        slot = pick_best_slot(duration, problem["qualified"][i], problem, classroom_booked,
                              teacher_booked, teacher_load, w_pref, w_bal, num_candidates)
        if slot is None:
            slot = [random.choice(gene_space[3 * i]),
                    random.choice(gene_space[3 * i + 1]),
                    random.choice(gene_space[3 * i + 2])]

        chromosome[3 * i:3 * i + 3] = slot
        end = slot[0] + duration
        classroom_booked.setdefault(slot[1], []).append((slot[0], end))
        teacher_booked.setdefault(slot[2], []).append((slot[0], end))
        teacher_load[slot[2]] += duration
    return chromosome


def create_soft_population(size, problem, weight_picker, num_candidates):
    population = []
    for _ in range(size):
        w_pref, w_bal = weight_picker()
        population.append(create_soft_chromosome(problem, w_pref, w_bal, num_candidates))
    return population


def pareto_indexes(points):
    keep = []
    for i in range(len(points)):
        dominated = False
        for j in range(len(points)):
            if i == j:
                continue
            no_worse = points[j][0] >= points[i][0] and points[j][1] >= points[i][1]
            better = points[j][0] > points[i][0] or points[j][1] > points[i][1]
            if no_worse and better:
                dominated = True
                break
        if not dominated:
            keep.append(i)
    return keep


def hypervolume_2d(points):
    feasible = []
    for point in points:
        if point[0] >= 0 and point[1] >= 0:
            feasible.append(point)
    if not feasible:
        return 0.0

    front = []
    for index in pareto_indexes(feasible):
        front.append(feasible[index])
    front.sort(key=lambda point: point[0], reverse=True)

    volume = 0.0
    previous_bal = 0.0
    for pref, bal in front:
        if bal > previous_bal:
            volume += pref * (bal - previous_bal)
            previous_bal = bal
    return volume