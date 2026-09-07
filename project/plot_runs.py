"""Plot the distance and word-length pairs in runs.csv."""

import csv
import math
from pathlib import Path
from statistics import fmean

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def read_runs(path: Path) -> tuple[list[int], list[int]]:
    lengths = []
    distances = []
    with path.open(newline="") as source:
        for line_number, row in enumerate(csv.reader(source), start=1):
            if not row:
                continue
            try:
                if len(row) != 2:
                    raise ValueError
                distance, length = map(int, row)
                if distance < 0 or length < 1:
                    raise ValueError
            except ValueError as error:
                raise ValueError(
                    f"{path}, line {line_number}: expected two integers "
                    "(distance >= 0, word length >= 1)."
                ) from error
            distances.append(distance)
            lengths.append(length)
    if not lengths:
        raise ValueError(f"{path} contains no runs.")
    return lengths, distances


def main() -> None:
    try:
        lengths, distances = read_runs(Path("runs.csv"))
    except (OSError, ValueError, csv.Error) as error:
        raise SystemExit(f"Could not read runs: {error}") from error

    print(f"Average distance: {fmean(distances):.4f}")
    print(f"Average length: {fmean(lengths):.4f}")
    print(f"Average sqrt(length): {fmean(math.sqrt(n) for n in lengths):.4f}")

    minimum, maximum = min(lengths), max(lengths)
    reference_n = [minimum + (maximum - minimum) * i / 500 for i in range(501)]
    roots = [math.sqrt(n) for n in reference_n]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(lengths, distances, s=8, alpha=0.15, label="Runs")
    marker = "o" if minimum == maximum else None
    ax.plot(reference_n, roots, label="√n", color="tab:orange", marker=marker)
    ax.set_xlabel("Number of characters (n)")
    ax.set_ylabel("Distance")
    ax.set_title("Distance by word length")
    ax.set_ylim(bottom=0)
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    try:
        fig.savefig("runs.png", dpi=200)
    except OSError as error:
        raise SystemExit(f"Could not save runs.png: {error}") from error
    finally:
        plt.close(fig)
    print("Saved runs.png")


if __name__ == "__main__":
    main()
