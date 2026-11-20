import numpy as np


def teacher_free(teacher, lectures):
    assigned_to_teacher = []
    for lecture in lectures:
        if lecture.teacher == teacher:
            assigned_to_teacher.append(lecture)

    assigned_to_teacher = sorted(assigned_to_teacher, key=lambda lecture: lecture.start_time)
    time_end_prev = 0
    for lecture in assigned_to_teacher:
        if lecture.start_time < time_end_prev:
            return False
        time_end_prev = lecture.start_time + lecture.duration

    return True


def teacher_qualified(teacher, lectures, teachers):
    assigned_to_teacher = []
    for lecture in lectures:
        if lecture.teacher == teacher:
            assigned_to_teacher.append(lecture)

    for lecture in assigned_to_teacher:
        if lecture.class_name not in teachers[teacher]:
            return False
    return True


def classroom_free(classroom, lectures, classrooms):
    classroom_open, classroom_close = classrooms[classroom]

    assigned_to_classroom = []
    for lecture in lectures:
        if lecture.classroom == classroom:
            assigned_to_classroom.append(lecture)

    assigned_to_classroom = sorted(assigned_to_classroom, key=lambda lecture: lecture.start_time)
    time_end_prev = classroom_open

    for lecture in assigned_to_classroom:
        if lecture.start_time < time_end_prev:
            return False
        time_end_prev = lecture.start_time + lecture.duration
        if time_end_prev > classroom_close:
            return False

    return True


def schedule_checker(classrooms, lectures, teachers):
    for lecture in lectures:
        if (
            lecture.start_time is None
            or lecture.classroom not in classrooms
            or lecture.teacher not in teachers
        ):
            return False

    for teacher in teachers:
        if not teacher_free(teacher, lectures):
            return False
        if not teacher_qualified(teacher, lectures, teachers):
            return False

    for classroom in classrooms:
        if not classroom_free(classroom, lectures, classrooms):
            return False

    return True


def all_classes(lectures, classes):
    counted = {}
    for lecture in lectures:
        name = lecture.class_name
        if name in counted:
            counted[name] += 1
        else:
            counted[name] = 1

    scheduled = []
    required = []
    for name in classes:
        if name in counted:
            scheduled.append(counted[name])
        else:
            scheduled.append(0)
        required.append(len(classes[name]))

    difference = np.abs(np.array(scheduled) - np.array(required))
    return difference


def overlap(start1, end1, start2, end2):
    return max(0, min(end1, end2) - max(start1, start2))


def collect_intervals(chromosome, unassigned_lectures, gene_offset):
    groups = {}
    for i in range(len(unassigned_lectures)):
        start = chromosome[3 * i]
        end = start + unassigned_lectures[i].duration
        key = chromosome[3 * i + gene_offset]
        groups.setdefault(key, []).append((start, end))
    return groups


def double_booked_hours(groups):
    total = 0
    for intervals in groups.values():
        intervals.sort()
        for a in range(len(intervals)):
            for b in range(a + 1, len(intervals)):
                if intervals[b][0] >= intervals[a][1]:
                    break
                total += overlap(intervals[a][0], intervals[a][1],
                                 intervals[b][0], intervals[b][1])
    return total


def outside_hours(chromosome, unassigned_lectures, classroom_hours):
    total = 0
    for i in range(len(unassigned_lectures)):
        start = chromosome[3 * i]
        duration = unassigned_lectures[i].duration
        open_time, close_time = classroom_hours[chromosome[3 * i + 1]]
        total += duration - overlap(start, start + duration, open_time, close_time)
    return total


def count_hard_violations(chromosome, unassigned_lectures, classroom_hours):
    total = outside_hours(chromosome, unassigned_lectures, classroom_hours)
    total += double_booked_hours(collect_intervals(chromosome, unassigned_lectures, 1))
    total += double_booked_hours(collect_intervals(chromosome, unassigned_lectures, 2))
    return total


def preference_score(chromosome, unassigned_lectures, teacher_windows):
    net = 0
    total = 0
    for i in range(len(unassigned_lectures)):
        start = chromosome[3 * i]
        duration = unassigned_lectures[i].duration
        likes, dislikes = teacher_windows[chromosome[3 * i + 2]]
        if likes is not None:
            net += overlap(start, start + duration, likes[0], likes[1])
        if dislikes is not None:
            net -= overlap(start, start + duration, dislikes[0], dislikes[1])
        total += duration
    if total == 0:
        return 0.5
    return 0.5 + 0.5 * net / total


def teacher_loads(chromosome, unassigned_lectures, num_teachers):
    loads = [0] * num_teachers
    for i in range(len(unassigned_lectures)):
        loads[chromosome[3 * i + 2]] += unassigned_lectures[i].duration
    return loads


def balance_score(loads):
    count = len(loads)
    if count < 2:
        return 1.0
    mean = sum(loads) / count
    if mean == 0:
        return 1.0
    worst = mean * np.sqrt(count - 1)
    return 1.0 - float(np.std(loads)) / worst


def soft_score(pref, bal, w_pref, w_bal):
    return (w_pref * pref + w_bal * bal) / (w_pref + w_bal)