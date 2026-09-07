from hypothesis import given
from hypothesis import strategies as st

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
