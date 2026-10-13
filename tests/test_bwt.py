from hypothesis import given
from hypothesis import strategies as st

from project.bwt import reconstruct, transform


def reference_transform(data: bytes) -> str:
    symbols = tuple(chr(byte + 1) for byte in data) + ("\0",)
    rotations = [symbols[i:] + symbols[:i] for i in range(len(symbols))]
    return "".join(rotation[-1] for rotation in sorted(rotations))


def test_known_transform() -> None:
    assert transform(b"banana") == "booc\0bb"


def test_empty_transform() -> None:
    assert transform(b"") == "\0"
    assert reconstruct("\0") == b""


def test_transform_supports_every_byte_value() -> None:
    data = bytes(range(256))
    assert reconstruct(transform(data)) == data


@given(st.binary(max_size=32))
def test_transform_matches_reference(data: bytes) -> None:
    assert transform(data) == reference_transform(data)


@given(st.binary())
def test_transform_then_reconstruct_gives_same_bytes(data: bytes) -> None:
    assert reconstruct(transform(data)) == data
