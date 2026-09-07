from project.bwt import reconstruct
from hypothesis import given
from hypothesis import strategies as st

from project.bwt import transform

@given(st.text(alphabet=st.characters(exclude_characters='\0')))
def test_transform_then_reconstruct_gives_same_string(text: str):
    assert reconstruct(transform(text)) == text
