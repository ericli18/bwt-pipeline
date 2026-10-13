"""SQLite storage for BWT experiments."""

import hashlib
import sqlite3
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path

from project.loaders import CorpusDocument
from project.substitution import SubstitutionChange

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY,
    corpus TEXT NOT NULL,
    name TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    content BLOB NOT NULL,
    length INTEGER NOT NULL CHECK (length >= 0),
    UNIQUE (corpus, name, sha256)
);

CREATE TABLE IF NOT EXISTS experiments (
    id INTEGER PRIMARY KEY,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    status TEXT NOT NULL CHECK (status IN ('running', 'completed')),
    corpus TEXT NOT NULL,
    replacement_policy TEXT NOT NULL,
    seed INTEGER NOT NULL,
    trials_per_document INTEGER NOT NULL CHECK (trials_per_document > 0)
);

CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY,
    experiment_id INTEGER NOT NULL REFERENCES experiments(id),
    document_id INTEGER NOT NULL REFERENCES documents(id),
    substitution_type TEXT NOT NULL CHECK (substitution_type IN ('group', 'window')),
    g INTEGER NOT NULL CHECK (g > 0),
    trial INTEGER NOT NULL CHECK (trial >= 0),
    distance INTEGER NOT NULL CHECK (distance >= 0),
    UNIQUE (experiment_id, document_id, substitution_type, g, trial)
);

CREATE INDEX IF NOT EXISTS runs_by_experiment
ON runs (experiment_id, substitution_type, g, document_id);

CREATE TABLE IF NOT EXISTS changes (
    id INTEGER PRIMARY KEY,
    run_id INTEGER NOT NULL REFERENCES runs(id),
    position INTEGER NOT NULL CHECK (position >= 0),
    original_byte INTEGER NOT NULL CHECK (original_byte BETWEEN 0 AND 255),
    replacement_byte INTEGER NOT NULL CHECK (replacement_byte BETWEEN 0 AND 255),
    UNIQUE (run_id, position)
);
"""


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(SCHEMA)
    return connection


def add_document(
    connection: sqlite3.Connection, corpus: str, document: CorpusDocument
) -> int:
    digest = hashlib.sha256(document.data).hexdigest()
    connection.execute(
        """
        INSERT OR IGNORE INTO documents (corpus, name, sha256, content, length)
        VALUES (?, ?, ?, ?, ?)
        """,
        (corpus, document.name, digest, document.data, len(document.data)),
    )
    row = connection.execute(
        "SELECT id FROM documents WHERE corpus = ? AND name = ? AND sha256 = ?",
        (corpus, document.name, digest),
    ).fetchone()
    if row is None:  # pragma: no cover - guards unexpected database corruption
        raise RuntimeError(f"Could not store document: {document.name}")
    return int(row[0])


def start_experiment(
    connection: sqlite3.Connection,
    *,
    corpus: str,
    seed: int,
    trials_per_document: int,
) -> int:
    cursor = connection.execute(
        """
        INSERT INTO experiments (
            started_at, status, corpus, replacement_policy, seed, trials_per_document
        ) VALUES (?, 'running', ?, 'uniform_observed_file_bytes', ?, ?)
        """,
        (datetime.now(UTC).isoformat(), corpus, seed, trials_per_document),
    )
    connection.commit()
    return int(cursor.lastrowid)


def add_run(
    connection: sqlite3.Connection,
    *,
    experiment_id: int,
    document_id: int,
    substitution_type: str,
    g: int,
    trial: int,
    changes: Iterable[SubstitutionChange],
    distance: int,
) -> None:
    cursor = connection.execute(
        """
        INSERT INTO runs (experiment_id, document_id, substitution_type, g, trial, distance)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (experiment_id, document_id, substitution_type, g, trial, distance),
    )
    connection.executemany(
        """
        INSERT INTO changes (run_id, position, original_byte, replacement_byte)
        VALUES (?, ?, ?, ?)
        """,
        (
            (
                cursor.lastrowid,
                change.position,
                change.original_byte,
                change.replacement_byte,
            )
            for change in changes
        ),
    )


def complete_experiment(connection: sqlite3.Connection, experiment_id: int) -> None:
    connection.execute(
        """
        UPDATE experiments
        SET status = 'completed', completed_at = ?
        WHERE id = ?
        """,
        (datetime.now(UTC).isoformat(), experiment_id),
    )
    connection.commit()
