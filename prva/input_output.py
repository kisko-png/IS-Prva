import ast
import random


def txt2dict(path):
    data = {}

    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue

            name, values = line.split(None, 1)
            values = (
                values.replace("“", '"')
                .replace("”", '"')
                .replace("‘", "'")
                .replace("’", "'")
            )

            try:
                data[name] = ast.literal_eval(values)
            except (ValueError, SyntaxError):
                values = values.strip().strip("[]")
                data[name] = [
                    item.strip().strip("'\"")
                    for item in values.split(",")
                    if item.strip()
                ]

    return data


def write_random_preferences(path, teacher_names, earliest, latest, seed):
    rng = random.Random(seed)
    lines = []

    for name in teacher_names:
        like_length = rng.randint(3, 5)
        like_start = rng.randint(earliest, latest - like_length)
        likes = [like_start, like_start + like_length]
        preference = {"likes": likes}

        if rng.random() < 0.7:
            dislike_length = rng.randint(2, 3)
            for _ in range(20):
                dislike_start = rng.randint(earliest, latest - dislike_length)
                dislikes = [dislike_start, dislike_start + dislike_length]
                if dislikes[1] <= likes[0] or dislikes[0] >= likes[1]:
                    preference["dislikes"] = dislikes
                    break

        lines.append(name + " " + str(preference).replace("'", '"'))

    with open(path, "w", encoding="utf-8") as file:
        file.write("\n".join(lines) + "\n")