import numpy as np
import matplotlib.pyplot as plt


def plot_pareto(single_points, fronts, path):
    plt.figure(figsize=(7.5, 6))

    for index, front in enumerate(fronts):
        pref = [point[0] for point in front]
        bal = [point[1] for point in front]
        label = "NSGA-II fronts (one per seed)" if index == 0 else None
        plt.scatter(pref, bal, marker="o", s=25, alpha=0.5, color="black", label=label)

    for label, points in single_points.items():
        pref = [point[0] for point in points]
        bal = [point[1] for point in points]
        plt.scatter(pref, bal, marker="x", s=70, label=label)

    plt.xlabel("Preference score")
    plt.ylabel("Balance score")
    plt.title("Feasible solutions: preference vs balance")
    plt.grid(linestyle="--", alpha=0.5)
    plt.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(path, dpi=150)


def plot_hypervolume(histories, path):
    plt.figure(figsize=(8, 5))

    for name, curves in histories.items():
        shortest = min(len(curve) for curve in curves)
        trimmed = []
        for curve in curves:
            trimmed.append(curve[:shortest])
        mean_curve = np.mean(trimmed, axis=0)
        plt.plot(np.arange(shortest), mean_curve, label=name)

    plt.xlabel("Generation")
    plt.ylabel("Hypervolume of feasible solutions")
    plt.title("Solution quality per generation")
    plt.grid(linestyle="--", alpha=0.5)
    plt.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(path, dpi=150)