import itertools
import sqlite3
from operator import itemgetter

from project import pipeline
from project.results import connect
from project.smooth import results
from project.smooth.sensitivity import (
    BETAS,
    DP_BETA,
    EPSILON,
    closed_form_bound,
    context_errors,
    cyclic_runs,
    d_indexed_bound,
    global_bound,
)


def latest_experiment_id(database: sqlite3.Connection) -> int:
    (experiment_id,) = database.execute("SELECT MAX(id) FROM experiments").fetchone()
    return experiment_id or 0


def analyze_document(database: sqlite3.Connection, document_id: int, name: str, data: bytes) -> int:
    bwt_runs = results.document_runs(database, document_id)
    
    if bwt_runs is not None: return bwt_runs

    n = len(data)
    bwt_runs = cyclic_runs(data)
    errors, ell = context_errors(data)
    gs = global_bound(n)
    results.add_document(database, document_id=document_id, bwt_runs=bwt_runs, ell=ell, global_bound=gs)
    
    for beta in BETAS:
        closed_form = closed_form_bound(errors, n, beta)
        results.add_bound(
            database,
            document_id=document_id,
            beta=beta,
            closed_form=closed_form,
            d_indexed=d_indexed_bound(errors, n, beta),
        )
        if beta == DP_BETA:
            noise_ratio = gs / (2 * closed_form[0] / EPSILON)
    print(
        f"Smooth sensitivity of {name} ({n:,} bytes): r={bwt_runs}, GS={gs:.0f}, "
        f"noise ratio={noise_ratio:.2f}"
    )
    return bwt_runs


def analyze_runs(database: sqlite3.Connection, experiment_id: int, document_id: int, data: bytes, bwt_runs: int,) -> None:
    changes = database.execute(
        """
        SELECT r.id, c.position, c.replacement_byte
        FROM runs r
        JOIN changes c ON c.run_id = r.id
        LEFT JOIN smooth_runs s ON s.run_id = r.id
        WHERE r.experiment_id = ? AND r.document_id = ? AND s.run_id IS NULL
        ORDER BY r.id
        """,
        (experiment_id, document_id),
    ).fetchall()
    
    for run_id, run_changes in itertools.groupby(changes, key=itemgetter(0)):
        edited = bytearray(data)
    
        for _, position, replacement_byte in run_changes: edited[position] = replacement_byte
        
        edited_runs = cyclic_runs(bytes(edited))
        results.add_run(
            database,
            run_id=run_id,
            bwt_runs=edited_runs,
            bwt_runs_change=edited_runs - bwt_runs,
        )


def analyze_experiment(database: sqlite3.Connection, experiment_id: int) -> None:
    results.create_tables(database)
    documents = database.execute(
        """
        SELECT id, name, content FROM documents
        WHERE id IN (SELECT DISTINCT document_id FROM runs WHERE experiment_id = ?)
        ORDER BY length
        """,
        (experiment_id,),
    ).fetchall()
    
    for document_id, name, data in documents:
        bwt_runs = analyze_document(database, document_id, name, data)
        analyze_runs(database, experiment_id, document_id, data, bwt_runs)
        database.commit()


def main() -> None:
    args = pipeline.parse_args()
    
    with connect(args.database) as database: previous_id = latest_experiment_id(database)

    pipeline.main()

    with connect(args.database) as database:
        row = database.execute(
            """
            SELECT id FROM experiments
            WHERE id > ? AND corpus = ? AND status = 'completed'
            ORDER BY id DESC
            """,
            (previous_id, args.corpus),
        ).fetchone()
        
        if row is None: raise RuntimeError("project.pipeline did not save a completed experiment")
        
        experiment_id = int(row[0])
        analyze_experiment(database, experiment_id)

    print(f"Saved smooth sensitivity for experiment {experiment_id} to {args.database}")


if __name__ == "__main__":
    main()
