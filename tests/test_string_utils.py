import random

from hypothesis import given
from hypothesis import strategies as st

from rapidfuzz.distance import Levenshtein

from project.string_utils import levenshtein_distance


@given(st.text(alphabet=st.characters(exclude_characters="\0")))
def test_distance_of_same_strings_are_same(text: str):
    assert levenshtein_distance(text, text) == 0


@given(
    st.text(alphabet=st.characters(exclude_characters="\0")),
    st.text(alphabet=st.characters(exclude_characters="\0")),
)
def test_text_with_n_extra_characters_is_n(text: str, suffix: str):
    assert levenshtein_distance(text, text + suffix) == len(suffix)


@given(st.binary(max_size=200), st.binary(max_size=200))
def test_banded_distance_matches_full_distance(a: bytes, b: bytes):
    assert levenshtein_distance(a, b) == Levenshtein.distance(a, b)


def test_banded_distance_is_exact_beyond_the_initial_cutoff():
    rng = random.Random(0)
    a = bytes(rng.randrange(256) for _ in range(2000))
    b = bytes(rng.randrange(256) for _ in range(1500))
    assert levenshtein_distance(a, b) == Levenshtein.distance(a, b)
