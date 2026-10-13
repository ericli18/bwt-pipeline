"""String-distance helpers."""

from collections.abc import Hashable, Sequence

from rapidfuzz.distance import Levenshtein

INITIAL_CUTOFF = 64


def levenshtein_distance(a: Sequence[Hashable], b: Sequence[Hashable]) -> int:
    """Return the exact unit-cost Levenshtein distance between two sequences.

    A cutoff lets rapidfuzz search only a band around the diagonal, which is far
    faster when the distance is small relative to the lengths. Above the cutoff
    rapidfuzz returns ``cutoff + 1``, so doubling until the result fits is exact.
    """
    cutoff = max(INITIAL_CUTOFF, abs(len(a) - len(b)))
    while (distance := Levenshtein.distance(a, b, score_cutoff=cutoff)) > cutoff:
        cutoff *= 2
    return distance
