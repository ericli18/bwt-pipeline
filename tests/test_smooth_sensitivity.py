import math
from collections import Counter, defaultdict

from hypothesis import given
from hypothesis import strategies as st

from project.smooth.sensitivity import (
    closed_form_bound,
    context_errors,
    cyclic_runs,
    d_indexed_bound,
    global_bound,
)


def rotations(data: bytes) -> list[int]:
    return sorted(range(len(data)), key=lambda i: data[i:] + data[:i])


def reference_runs(data: bytes) -> int:
    labels = [data[i - 1] for i in rotations(data)]
    return sum(1 for k, label in enumerate(labels) if k == 0 or label != labels[k - 1])


def reference_errors(data: bytes, h: int) -> int:
    n = len(data)
    contexts = defaultdict(Counter)
    for i in range(n):
        contexts[(data + data)[i : i + h]][data[i - 1]] += 1
    return sum(c.total() - max(c.values()) for c in contexts.values())


def test_known_runs() -> None:
    # Sorted rotations of banana end in n, n, b, a, a, a
    assert cyclic_runs(b"banana") == 3


@given(st.binary(min_size=1, max_size=40))
def test_runs_match_reference(data: bytes) -> None:
    assert cyclic_runs(data) == reference_runs(data)


@given(st.binary(min_size=1, max_size=40).filter(lambda d: len(set(d)) <= 4))
def test_context_errors_match_reference(data: bytes) -> None:
    errors, ell = context_errors(data)
    n = len(data)
    assert len(errors) == min(ell, n - 1) + 1
    for h in range(n):
        expected = reference_errors(data, h)
        assert (errors[h] if h < len(errors) else 0) == expected
        assert (expected > 0) == (h < ell)


@given(st.integers(min_value=1, max_value=3000))
def test_global_bound_matches_brute_force(n: int) -> None:
    c = n * math.floor(math.log2(n))
    expected = 2 * min(h + 1 + c / (h + 1) for h in range(n))
    assert math.isclose(global_bound(n), expected)


@given(st.binary(min_size=2, max_size=40), st.floats(min_value=0.01, max_value=2))
def test_smooth_bounds_cover_bwt_runs_change(data: bytes, beta: float) -> None:
    errors, _ = context_errors(data)
    n = len(data)
    bound = min(closed_form_bound(errors, n, beta)[0], d_indexed_bound(errors, n, beta)[0])
    r = cyclic_runs(data)
    for position in range(n):
        for byte in set(data) - {data[position]}:
            edited = data[:position] + bytes([byte]) + data[position + 1 :]
            assert abs(cyclic_runs(edited) - r) <= bound
