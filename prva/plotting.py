import numpy as np
import matplotlib.pyplot as plt


def plot_pareto(single_points, fronts, path):
    figure, axis = plt.subplots(figsize=(7.5, 6))

    for index, front in enumerate(fronts):
        pref = [point[0] for point in front]
        bal = [point[1] for point in front]
        label = "NSGA-II fronts (one per seed)" if index == 0 else None
        axis.scatter(pref, bal, marker="o", s=25, alpha=0.5, color="black", label=label)

    for label, points in single_points.items():
        pref = [point[0] for point in points]
        bal = [point[1] for point in points]
        axis.scatter(pref, bal, marker="x", s=70, label=label)

    axis.set_xlabel("Preference score")
    axis.set_ylabel("Balance score")
    axis.set_title("Feasible solutions: preference vs balance")
    axis.grid(linestyle="--", alpha=0.5)
    axis.legend(fontsize=8)
    figure.tight_layout()
    figure.savefig(path, dpi=150)
    plt.close(figure)


def plot_hypervolume(histories, path):
    figure, axis = plt.subplots(figsize=(8, 5))

    for name, curves in histories.items():
        shortest = min(len(curve) for curve in curves)
        trimmed = []
        for curve in curves:
            trimmed.append(curve[:shortest])
        mean_curve = np.mean(trimmed, axis=0)
        axis.plot(np.arange(1, shortest + 1), mean_curve, label=name)

    axis.set_xlabel("Generation")
    axis.set_ylabel("Hypervolume of feasible solutions")
    axis.set_title("Solution quality per generation")
    axis.grid(linestyle="--", alpha=0.5)
    axis.legend(fontsize=8)
    figure.tight_layout()
    figure.savefig(path, dpi=150)
    plt.close(figure)


def mean_step_curve(runs, grid):
    stacked = []
    for xs, ys in runs:
        index = np.searchsorted(xs, grid, side="right") - 1
        index = np.clip(index, 0, len(ys) - 1)
        stacked.append(np.asarray(ys)[index])
    return np.mean(stacked, axis=0)


def plot_curve_panels(panels, x_label, y_label, path, use_time=False):
    count = len(panels)
    columns = 2 if count > 1 else 1
    rows = (count + columns - 1) // columns
    figure, axes = plt.subplots(rows, columns, figsize=(6.5 * columns, 4.2 * rows), squeeze=False)

    for position, title in enumerate(panels):
        axis = axes[position // columns][position % columns]
        longest = 0.0
        for runs in panels[title].values():
            for xs, ys in runs:
                longest = max(longest, xs[-1])

        if use_time:
            first_observation = max(
                xs[0]
                for runs in panels[title].values()
                for xs, _ in runs
            )
            grid = np.linspace(first_observation, longest, 300)
        else:
            grid = np.arange(1, int(longest) + 1)

        for label, runs in panels[title].items():
            axis.plot(grid, mean_step_curve(runs, grid), label=label)

        axis.set_title(title)
        axis.set_xlabel(x_label)
        axis.set_ylabel(y_label)
        axis.grid(linestyle="--", alpha=0.5)
        axis.legend(fontsize=8)

    for position in range(count, rows * columns):
        axes[position // columns][position % columns].axis("off")

    figure.tight_layout()
    figure.savefig(path, dpi=150)
    plt.close(figure)


def plot_bar_panels(panels, y_label, path):
    count = len(panels)
    columns = 2 if count > 1 else 1
    rows = (count + columns - 1) // columns
    figure, axes = plt.subplots(rows, columns, figsize=(6.5 * columns, 4.2 * rows), squeeze=False)

    for position, title in enumerate(panels):
        axis = axes[position // columns][position % columns]
        labels, values, notes = panels[title]
        axis.bar(np.arange(len(labels)), values, color="tab:blue", alpha=0.8)
        for index in range(len(labels)):
            axis.text(index, values[index], notes[index], ha="center", va="bottom", fontsize=8)
        axis.set_xticks(np.arange(len(labels)))
        axis.set_xticklabels(labels, rotation=25, ha="right", fontsize=8)
        axis.set_ylabel(y_label)
        axis.set_title(title)
        axis.grid(axis="y", linestyle="--", alpha=0.5)

    for position in range(count, rows * columns):
        axes[position // columns][position % columns].axis("off")

    figure.tight_layout()
    figure.savefig(path, dpi=150)
    plt.close(figure)
