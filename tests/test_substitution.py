import random

import pytest
from hypothesis import given
from hypothesis import strategies as st

from project.substitution import GroupSubstitution, WindowSubstitution


@pytest.mark.parametrize("strategy", [GroupSubstitution, WindowSubstitution])
@given(
    data=st.binary(min_size=2, max_size=30).filter(lambda data: len(set(data)) >= 2),
    seed=st.integers(),
    g=st.integers(min_value=1, max_value=30),
)
def test_multiple_substitutions_change_exactly_g_bytes(strategy, data, seed, g):
    if g > len(data):
        return
    substitution = strategy(data, random.Random(seed), g)
    result = substitution.substitute()
    positions = [change.position for change in result.changes]

    assert len(result.data) == len(data)
    assert len(result.changes) == g
    assert positions == sorted(set(positions))
    assert [
        index
        for index, (before, after) in enumerate(zip(data, result.data))
        if before != after
    ] == positions
    for change in result.changes:
        assert change.original_byte == data[change.position]
        assert change.replacement_byte == result.data[change.position]
        assert change.replacement_byte in substitution.alphabet
    if strategy is WindowSubstitution:
        assert positions == list(range(positions[0], positions[0] + g))
    assert substitution.data == data
