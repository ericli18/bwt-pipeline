"""Plot BWT distance against text length, next to each strategy's hypothesized bound."""

import argparse
import math
import sqlite3
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from project.bounds import BOUNDS, bound_ratio
from project.pipeline import DATABASE_PATH, G_VALUES, SUBSTITUTIONS

# Reference categorical slots 1-3, with distinct markers so identity is not
# carried by color alone.
G_STYLES = {
    1: {"color": "#2a78d6", "marker": "o"},
    10: {"color": "#eb6834", "marker": "s"},
    100: {"color": "#1baf7a", "marker": "^"},
}
INK = "#52514e"
FILE_LABEL_SIZE = 7
DEFAULT_OUTPUT = Path("runs.png")


@dataclass(frozen=True)
class Experiment:
    id: int
    corpus: str
    seed: int
    trials_per_document: int


@dataclass(frozen=True)
class Run:
    corpus: str
    file: str
    n: int
    substitution_type: str
    g: int
    distance: int

    @property
    def ratio(self) -> float:
        return bound_ratio(self.substitution_type, self.g, self.n, self.distance)


def load_experiments(
    database: sqlite3.Connection, experiment_ids: list[int] | None
) -> list[Experiment]:
    columns = "id, corpus, seed, trials_per_document"
    if experiment_ids:
        rows = []
        for experiment_id in experiment_ids:
            row = database.execute(
                f"SELECT {columns} FROM experiments WHERE id = ?", (experiment_id,)
            ).fetchone()
            if row is None:
                raise ValueError(f"Could not find experiment {experiment_id}")
            rows.append(row)
    else:
        # The latest completed experiment of every corpus.
        rows = database.execute(
            f"""
            SELECT {columns} FROM experiments
            WHERE id IN (
                SELECT MAX(id) FROM experiments
                WHERE status = 'completed' GROUP BY corpus
            )
            ORDER BY corpus
            """
        ).fetchall()
        if not rows:
            raise ValueError("Could not find a completed experiment")
    return [Experiment(*row) for row in rows]


def load_runs(database: sqlite3.Connection, experiments: list[Experiment]) -> list[Run]:
    runs = []
    for experiment in experiments:
        rows = database.execute(
            """
            SELECT documents.name, documents.length, runs.substitution_type,
                   runs.g, runs.distance
            FROM runs
            JOIN documents ON documents.id = runs.document_id
            WHERE runs.experiment_id = ?
            """,
            (experiment.id,),
        )
        runs.extend(Run(experiment.corpus, *row) for row in rows)
    if not runs:
        raise ValueError("The selected experiments contain no runs")
    return runs


def style_axis(ax: plt.Axes) -> None:
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.grid(alpha=0.25, which="major")
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)


def spread(positions: list[float], gap: float) -> list[float]:
    """Move sorted positions in [0, 1] apart until neighbors are at least gap apart."""
    spread_positions = list(positions)
    for i in range(1, len(spread_positions)):
        spread_positions[i] = max(spread_positions[i], spread_positions[i - 1] + gap)
    spread_positions[-1] = min(spread_positions[-1], 1.0)
    for i in range(len(spread_positions) - 2, -1, -1):
        spread_positions[i] = min(spread_positions[i], spread_positions[i + 1] - gap)
    return spread_positions


def label_files(ax: plt.Axes, files: dict[int, list[str]]) -> None:
    """Name every file under the x-axis, with a leader line to its length n."""
    lengths = sorted(files)
    low, high = math.log10(lengths[0]) - 0.08, math.log10(lengths[-1]) + 0.08
    ax.set_xlim(10**low, 10**high)
    ax.set_xticks([], minor=False)
    ax.set_xticks([], minor=True)
    for n in lengths:
        ax.axvline(n, color=INK, alpha=0.12, linewidth=0.8, zorder=0)

    fig = ax.get_figure()
    axes_width = ax.get_position().width * fig.get_figwidth()
    label_gap = FILE_LABEL_SIZE * 1.5 / 72 / axes_width
    targets = [(math.log10(n) - low) / (high - low) for n in lengths]
    for n, target, placed in zip(lengths, targets, spread(targets, label_gap)):
        ax.annotate(
            f"{' / '.join(files[n])}  {n:,}",
            xy=(target, 0),
            xycoords="axes fraction",
            xytext=(placed, -0.06),
            textcoords="axes fraction",
            rotation=90,
            ha="center",
            va="top",
            fontsize=FILE_LABEL_SIZE,
            color=INK,
            annotation_clip=False,
            arrowprops={
                "arrowstyle": "-",
                "color": INK,
                "alpha": 0.4,
                "linewidth": 0.6,
                "shrinkA": 0,
                "shrinkB": 0,
            },
        )


def plot(runs: list[Run], experiments: list[Experiment], output: Path) -> None:
    by_panel: dict[tuple[str, int], list[Run]] = defaultdict(list)
    files: dict[int, list[str]] = defaultdict(list)
    for run in runs:
        by_panel[run.substitution_type, run.g].append(run)
        if run.file not in files[run.n]:
            files[run.n].append(run.file)
    lengths = sorted(files)
    curve_n = [lengths[0] * (lengths[-1] / lengths[0]) ** (i / 200) for i in range(201)]

    substitution_types = [s for s in SUBSTITUTIONS if any(k[0] == s for k in by_panel)]
    fig, axes = plt.subplots(
        1,
        len(substitution_types),
        figsize=(9 * len(substitution_types), 8),
        squeeze=False,
    )
    # Fixed margins leave room for the file labels under each axis.
    fig.subplots_adjust(left=0.05, right=0.99, top=0.84, bottom=0.25, wspace=0.12)
    for ax, substitution_type in zip(axes[0], substitution_types):
        bound_label, bound = BOUNDS[substitution_type]

        for g in G_VALUES:
            panel = by_panel.get((substitution_type, g))
            if not panel:
                continue
            style = G_STYLES[g]

            per_file: dict[tuple[str, str], list[Run]] = defaultdict(list)
            for run in panel:
                per_file[run.corpus, run.file].append(run)
            worst = [
                max(file_runs, key=lambda run: run.distance)
                for file_runs in per_file.values()
            ]

            ax.scatter(
                [r.n for r in panel],
                [r.distance for r in panel],
                color=style["color"],
                marker=style["marker"],
                s=10,
                alpha=0.15,
                linewidths=0,
            )
            ax.plot(
                [r.n for r in worst],
                [r.distance for r in worst],
                color=style["color"],
                marker=style["marker"],
                markersize=8,
                linewidth=0,
                markeredgecolor="white",
                markeredgewidth=1,
            )
            ax.plot(
                curve_n,
                [bound(g, n) for n in curve_n],
                color=style["color"],
                linestyle="--",
                linewidth=1.5,
            )

        ax.set_title(
            f"{substitution_type.capitalize()} substitution, bound {bound_label}"
        )
        ax.set_ylabel("BWT Levenshtein distance d (log scale)")
        ax.set_xlabel("File, positioned by length n in bytes (log scale)", labelpad=100)
        style_axis(ax)
        ax.grid(False, axis="x")
        label_files(ax, files)

    handles = [
        Line2D(
            [],
            [],
            color=G_STYLES[g]["color"],
            marker=G_STYLES[g]["marker"],
            markersize=8,
            linewidth=0,
            label=f"g = {g}",
        )
        for g in G_VALUES
    ] + [
        Line2D(
            [],
            [],
            color=INK,
            marker="o",
            markersize=4,
            alpha=0.3,
            linewidth=0,
            label="each trial",
        ),
        Line2D(
            [],
            [],
            color=INK,
            marker="o",
            markersize=8,
            linewidth=0,
            label="worst trial per file",
        ),
        Line2D([], [], color=INK, linestyle="--", label="hypothesized bound"),
    ]
    fig.legend(
        handles=handles,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.94),
        ncol=len(handles),
        frameon=False,
    )

    described = ", ".join(
        f"{e.corpus} (experiment {e.id}, seed {e.seed}, {e.trials_per_document} trials)"
        for e in experiments
    )
    fig.suptitle(f"BWT distance after g substitutions: {described}")

    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        fig.savefig(output, dpi=200)
    except OSError as error:
        raise SystemExit(f"Could not save {output}: {error}") from error
    finally:
        plt.close(fig)
    print(f"Saved {output}")


def summarize(runs: list[Run]) -> None:
    """Print the worst observed d / bound per strategy and g."""
    worst: dict[tuple[str, int], Run] = {}
    for run in runs:
        key = run.substitution_type, run.g
        if key not in worst or run.ratio > worst[key].ratio:
            worst[key] = run
    print(f"{'strategy':<8} {'g':>4} {'max d/bound':>12}  worst file")
    for (substitution_type, g), run in sorted(worst.items()):
        print(
            f"{substitution_type:<8} {g:>4} {run.ratio:>12.3f}  "
            f"{run.corpus}/{run.file} (n={run.n:,}, d={run.distance:,})"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=DATABASE_PATH)
    parser.add_argument(
        "--experiment-id",
        type=int,
        action="append",
        help="repeatable; defaults to the latest completed experiment of each corpus",
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        with sqlite3.connect(f"file:{args.database}?mode=ro", uri=True) as database:
            experiments = load_experiments(database, args.experiment_id)
            runs = load_runs(database, experiments)
    except (OSError, sqlite3.Error, ValueError) as error:
        raise SystemExit(f"Could not read runs: {error}") from error

    plot(runs, experiments, args.output)
    summarize(runs)


if __name__ == "__main__":
    main()
