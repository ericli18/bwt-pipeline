"""Burrows-Wheeler transform for arbitrary byte strings."""

import numpy as np
from numpy.typing import NDArray
from pydivsufsort import divsufsort

SENTINEL = "\0"


def transform(data: bytes) -> str:
    if not data:
        return SENTINEL

    source = np.frombuffer(data, dtype=np.uint8)
    # Positional indexes of final characters in lexicographically sorted order
    # Basically, where each thing is in the last column of BWT
    suffix_array: NDArray[np.int32 | np.int64] = divsufsort(data)


    # Building BWT from array
    output = np.empty(len(data) + 1, dtype=np.uint16)

    #cast all bytes from 0-255 to 1-256, so 0 is sentinel
    output[0] = int(source[-1]) + 1

    output[1:] = source[suffix_array - 1].astype(np.uint16) + 1
    output[1:][suffix_array == 0] = 0

    return output.astype("<u2", copy=False).tobytes().decode("utf-16-le")


def reconstruct(bwt: str) -> bytes:
    if bwt.count(SENTINEL) != 1:
        raise ValueError("BWT must contain exactly one sentinel")
    if any(ord(symbol) > 256 for symbol in bwt):
        raise ValueError("BWT contains a symbol outside the byte alphabet")

    counts: dict[str, int] = {}
    for symbol in bwt:
        counts[symbol] = counts.get(symbol, 0) + 1

    offsets: dict[str, int] = {}
    total = 0
    for symbol in sorted(counts):
        offsets[symbol] = total
        total += counts[symbol]

    seen: dict[str, int] = {}
    ranks = []
    for symbol in bwt:
        ranks.append(seen.get(symbol, 0))
        seen[symbol] = seen.get(symbol, 0) + 1

    row = bwt.index(SENTINEL)
    output = []
    for _ in range(len(bwt) - 1):
        symbol = bwt[row]
        row = offsets[symbol] + ranks[row]
        output.append(bwt[row])

    return bytes(ord(symbol) - 1 for symbol in reversed(output))
