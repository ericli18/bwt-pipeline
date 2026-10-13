import argparse
import random
from pathlib import Path

from project.bwt import transform
from project.loaders import CORPORA, CorpusLoader
from project.results import (
    add_document,
    add_run,
    complete_experiment,
    connect,
    start_experiment,
)
from project.string_utils import levenshtein_distance
from project.substitution import GroupSubstitution, WindowSubstitution

DEFAULT_TRIALS = 100
DEFAULT_SEED = 0
DATABASE_PATH = Path("results.sqlite3")
SUBSTITUTIONS = {"group": GroupSubstitution, "window": WindowSubstitution}
G_VALUES = (1, 10, 100)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Measure how substituting g bytes changes the BWT of every file in a corpus, "
            f"for g in {G_VALUES}."
        )
    )
    parser.add_argument("--corpus", choices=CORPORA, required=True)
    parser.add_argument(
        "--substitution",
        choices=SUBSTITUTIONS,
        action="append",
        help="repeatable; defaults to every strategy",
    )
    parser.add_argument("--trials", type=int, default=DEFAULT_TRIALS)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--database", type=Path, default=DATABASE_PATH)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.trials < 1:
        raise SystemExit("--trials must be at least 1")

    corpus = CORPORA[args.corpus]
    substitution_types = args.substitution or list(SUBSTITUTIONS)
    with connect(args.database) as database:
        experiment_id = start_experiment(
            database,
            corpus=corpus.name,
            seed=args.seed,
            trials_per_document=args.trials,
        )
        print(f"Started experiment {experiment_id} on the {corpus.name} corpus")

        run_count = 0
        for document in CorpusLoader(corpus):
            data = document.data
            if not data:
                raise RuntimeError(f"Corpus file is empty: {document.name}")

            document_id = add_document(database, corpus.name, document)
            original_bwt = transform(data)

            for substitution_type in substitution_types:
                strategy = SUBSTITUTIONS[substitution_type]
                for g in G_VALUES:
                    # Each (seed, corpus, document, strategy, g) gets its own stream so
                    # its edits do not depend on the trial count or other documents.
                    rng = random.Random(
                        f"{args.seed}:{corpus.name}:{document.name}:{substitution_type}:{g}"
                    )
                    try:
                        substitution = strategy(data, rng, g)
                    except ValueError as exc:
                        raise RuntimeError(
                            f"Cannot substitute {g} bytes in {document.name}"
                        ) from exc

                    for trial in range(args.trials):
                        result = substitution.substitute()
                        distance = levenshtein_distance(
                            original_bwt, transform(result.data)
                        )
                        add_run(
                            database,
                            experiment_id=experiment_id,
                            document_id=document_id,
                            substitution_type=substitution_type,
                            g=g,
                            trial=trial,
                            changes=result.changes,
                            distance=distance,
                        )
                    run_count += args.trials

                    database.commit()
                    print(
                        f"Completed {document.name} ({len(data):,} bytes), "
                        f"{substitution_type}, g={g}: {args.trials} trials"
                    )

        complete_experiment(database, experiment_id)

    print(f"Saved experiment {experiment_id} with {run_count} runs to {args.database}")


if __name__ == "__main__":
    main()
