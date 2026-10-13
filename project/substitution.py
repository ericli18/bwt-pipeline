"""Strategies for substituting bytes in a document."""

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class SubstitutionChange:
    position: int
    original_byte: int
    replacement_byte: int


@dataclass(frozen=True)
class SubstitutionResult:
    data: bytes
    changes: tuple[SubstitutionChange, ...]


class BaseSubstitution(ABC):
    def __init__(self, data: bytes, rng: random.Random):
        self.data = data
        self.rng = rng
        self.alphabet = tuple(sorted(set(data)))
        if len(self.alphabet) < 2:
            raise ValueError("substitution requires at least two distinct bytes")

    def choose_replacement(self, original: int) -> int:
        replacements = tuple(symbol for symbol in self.alphabet if symbol != original)
        return self.rng.choice(replacements)

    def substitute_positions(self, positions: list[int] | range) -> SubstitutionResult:
        edited = bytearray(self.data)
        changes = []
        for position in positions:
            original = self.data[position]
            replacement = self.choose_replacement(original)
            edited[position] = replacement
            changes.append(SubstitutionChange(position, original, replacement))
        return SubstitutionResult(bytes(edited), tuple(changes))

    @abstractmethod
    def substitute(self) -> SubstitutionResult:
        """Return edited data and the change made to it."""


class GroupSubstitution(BaseSubstitution):
    def __init__(self, data: bytes, rng: random.Random, g: int):
        super().__init__(data, rng)
        if not 1 <= g <= len(data):
            raise ValueError("g must be between 1 and the data length")
        self.g = g

    def substitute(self) -> SubstitutionResult:
        positions = sorted(self.rng.sample(range(len(self.data)), self.g))
        return self.substitute_positions(positions)


class WindowSubstitution(GroupSubstitution):
    def substitute(self) -> SubstitutionResult:
        start = self.rng.randrange(len(self.data) - self.g + 1)
        return self.substitute_positions(range(start, start + self.g))
