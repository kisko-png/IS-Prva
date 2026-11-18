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
        if lecture.start_time is None or lecture.classroom is None:
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