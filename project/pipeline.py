import argparse
import random

from project.bwt import transform
from project.loaders import CORPORA, CorpusLoader
from project.string_utils import levenshtein_distance
from project.substitution import GroupSubstitution, WindowSubstitution

DEFAULT_TRIALS = 100
DEFAULT_SEED = 0
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
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.trials < 1:
        raise SystemExit("--trials must be at least 1")

    corpus = CORPORA[args.corpus]
    substitution_types = args.substitution or list(SUBSTITUTIONS)
    print(f"Started experiment on the {corpus.name} corpus")

    run_count = 0
    for document in CorpusLoader(corpus):
        data = document.data
        if not data:
            raise RuntimeError(f"Corpus file is empty: {document.name}")

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

                for _ in range(args.trials):
                    result = substitution.substitute()
                    levenshtein_distance(original_bwt, transform(result.data))
                run_count += args.trials

                print(
                    f"Completed {document.name} ({len(data):,} bytes), "
                    f"{substitution_type}, g={g}: {args.trials} trials"
                )

    print(f"Completed experiment with {run_count} runs")


if __name__ == "__main__":
    main()
