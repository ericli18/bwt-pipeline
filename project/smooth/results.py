import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS smooth_documents (
    document_id INTEGER PRIMARY KEY REFERENCES documents(id),
    bwt_runs INTEGER NOT NULL CHECK (bwt_runs >= 0),
    ell INTEGER NOT NULL CHECK (ell >= 0),
    global_bound REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS smooth_bounds (
    id INTEGER PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES smooth_documents(document_id),
    beta REAL NOT NULL CHECK (beta > 0),
    closed_form_bound REAL NOT NULL,
    closed_form_h INTEGER NOT NULL CHECK (closed_form_h >= 0),
    d_indexed_bound REAL NOT NULL,
    d_indexed_d INTEGER NOT NULL CHECK (d_indexed_d >= 0),
    UNIQUE (document_id, beta)
);

CREATE TABLE IF NOT EXISTS smooth_runs (
    run_id INTEGER PRIMARY KEY REFERENCES runs(id),
    bwt_runs INTEGER NOT NULL CHECK (bwt_runs >= 0),
    bwt_runs_change INTEGER NOT NULL
);
"""


def create_tables(connection: sqlite3.Connection) -> None:
    connection.executescript(SCHEMA)


def document_runs(connection: sqlite3.Connection, document_id: int) -> int | None:
    row = connection.execute("SELECT bwt_runs FROM smooth_documents WHERE document_id = ?", (document_id,)).fetchone()
    return None if row is None else int(row[0])


def add_document(connection: sqlite3.Connection, *, document_id: int, bwt_runs: int, ell: int, global_bound: float) -> None:
    connection.execute(
        """
        INSERT INTO smooth_documents (document_id, bwt_runs, ell, global_bound)
        VALUES (?, ?, ?, ?)
        """,
        (document_id, bwt_runs, ell, global_bound),
    )


def add_bound(connection: sqlite3.Connection, *, document_id: int, beta: float, closed_form: tuple[float, int], d_indexed: tuple[float, int]) -> None:
    connection.execute(
        """
        INSERT INTO smooth_bounds (
            document_id, beta, closed_form_bound, closed_form_h, d_indexed_bound, d_indexed_d
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (document_id, beta, *closed_form, *d_indexed),
    )


def add_run(connection: sqlite3.Connection, *, run_id: int, bwt_runs: int, bwt_runs_change: int) -> None:
    connection.execute(
        "INSERT INTO smooth_runs (run_id, bwt_runs, bwt_runs_change) VALUES (?, ?, ?)",
        (run_id, bwt_runs, bwt_runs_change),
    )
