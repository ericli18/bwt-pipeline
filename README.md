# bwt-pipeline

Each file is processed as bytes. Since most files are ASCII, this is equivalent to characters, but it also handles the binary files. For the subtitution, we only take bytes that are currently in the paper
## Running experiments

```console
uv run python -m project.pipeline --corpus calgary
uv run python -m project.pipeline --corpus canterbury
```

For some more control
```console
uv run python -m project.pipeline --corpus canterbury --substitution group \
  --trials 10 --seed 42
```

We also can query from the database:

```console
sqlite3 results.sqlite3 \
  "SELECT corpus, name, length FROM documents ORDER BY corpus, length;"

sqlite3 results.sqlite3 \
  "SELECT d.name, r.substitution_type, r.g, AVG(r.distance), MAX(r.distance)
   FROM runs r JOIN documents d ON d.id = r.document_id
   WHERE r.experiment_id = 1
   GROUP BY d.name, r.substitution_type, r.g ORDER BY d.length, r.g;"

sqlite3 results.sqlite3 \
  "SELECT r.trial, c.position, c.original_byte, c.replacement_byte
   FROM runs r JOIN changes c ON c.run_id = r.id
   WHERE r.experiment_id = 1 AND r.substitution_type = 'window' AND r.g = 10
   ORDER BY r.trial, c.position;"
```

## Plot the results

*NOTE: Everything below is LLM, I didn't want to generate any plots*

```console
uv run python -m project.plot_runs
```

By default this combines the latest completed experiment of each corpus, so both
corpora contribute points along n. Pick experiments explicitly with
`--experiment-id` (repeatable), and the file with `--output`.

There is one panel per strategy, plotting d against n on log-log axes with the
hypothesized bound for each g dashed in the same color. Each file is a labeled
vertical guide under the axis (name and length), so every stack of points can be
traced to its file. Faint points are single trials and solid markers are the worst
trial per file. The command also prints the worst observed d / bound for each
strategy and g, where anything above 1 is a counterexample.

## Test the BWT

```console
uv run python -m pytest
```
