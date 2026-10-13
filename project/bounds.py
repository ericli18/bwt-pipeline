"""Hypothesized upper bounds on the BWT Levenshtein distance after substituting
g bytes with a strategy"""
# TODO: Switch to Hamming lol

import math

# TODO: use tight bounds with constants instead
BOUNDS = {
    "group": ("√(gn)", lambda g, n: math.sqrt(g * n)),
    "window": ("g + √n", lambda g, n: g + math.sqrt(n)),
}


def bound_ratio(substitution_type: str, g: int, n: int, distance: int) -> float:
    return distance / BOUNDS[substitution_type][1](g, n)
