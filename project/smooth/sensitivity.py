import math

import numpy as np
from numpy.typing import NDArray
from pydivsufsort import divsufsort, kasai

EPSILON = 1.0
DELTA = 1e-6
DP_BETA = EPSILON / (2 * math.log(2 / DELTA))
BETAS = (DP_BETA, 0.1, 0.5)


def cyclic_runs(data: bytes) -> int:
    n = len(data)
    if n == 0:
        return 0

    suffix_array = divsufsort(data + data)
    rotations = suffix_array[suffix_array < n]
    labels = np.frombuffer(data, dtype=np.uint8)[rotations - 1]
    return 1 + int(np.count_nonzero(labels[1:] != labels[:-1]))


def context_errors(data: bytes) -> tuple[NDArray[np.int64], int]:
    n = len(data)
    doubled = data + data
    suffix_array = divsufsort(doubled)
    lcp = kasai(doubled, suffix_array)
    slots = np.flatnonzero(suffix_array < n)
    rotations = suffix_array[slots]
    labels = np.frombuffer(data, dtype=np.uint8)[rotations - 1].tolist()

    if n > 1:
        adjacent = np.minimum(np.minimum.reduceat(lcp[: slots[-1]], slots[:-1]), n)
    else:
        adjacent = np.zeros(0, dtype=np.int64)

    max_lcp = int(adjacent.max()) if adjacent.size else 0
    order = np.argsort(-adjacent, kind="stable").tolist()
    order_lcp = adjacent[order].tolist()

    parent = list(range(n))
    counts = [{label: 1} for label in labels]
    modal = [1] * n
    total_modal = n

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    errors = np.zeros(max_lcp + 2, dtype=np.int64)
    k = 0
    for h in range(max_lcp, -1, -1):
        while k < len(order) and order_lcp[k] == h:
            a, b = find(order[k]), find(order[k] + 1)
            k += 1
            if len(counts[a]) < len(counts[b]):
                a, b = b, a
            total_modal -= modal[a] + modal[b]
            merged = modal[a]
            for label, count in counts[b].items():
                total = counts[a].get(label, 0) + count
                counts[a][label] = total
                merged = max(merged, total)
            counts[b] = {}
            parent[b] = a
            modal[a] = merged
            total_modal += merged
        errors[h] = n - total_modal

    nonzero = np.flatnonzero(errors)
    ell = int(nonzero[-1]) + 1 if nonzero.size else 0
    return errors[: min(ell, n - 1) + 1], ell


def global_bound(n: int) -> float:
    c = n * (n.bit_length() - 1)

    root = math.isqrt(c)
    return 2 * min(k + c / k for k in (root, root + 1) if 1 <= k <= n)


def closed_form_bound(errors: NDArray[np.int64], n: int, beta: float) -> tuple[float, int]:
    a = max(1.0, 1.0 / math.expm1(beta))
    values = a * np.arange(1, len(errors) + 1) + errors
    h = int(np.argmin(values))
    return min(n - 1, 2 * float(values[h])), h


def d_indexed_bound(errors: NDArray[np.int64], n: int, beta: float) -> tuple[float, int]:
    contexts = np.arange(1, len(errors) + 1)
    best, best_d = 0.0, 0
    for d in range(n + 1):
        u = min(n - 1, 2 * int(np.min((d + 1) * contexts + errors)))
        value = math.exp(-beta * d) * u
        if value > best: best, best_d = value, d
        elif value < best: break
        if u >= n - 1: break
    return best, best_d
