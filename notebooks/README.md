# notebooks/

Exploratory instrumentation for
[EXP-001](../docs/experiments/exp-001-data-feasibility.md). Everything in this
directory is exploratory and sits **outside the ADR-003 layer contracts**: it is
not part of the package, nothing under `src/` imports it, and it does not import
the package. It is also outside mypy's `files`, though every signature is
annotated.

## Reproduce

```bash
uv sync --group eda
uv run --group eda python notebooks/eda_helpers.py --selftest        # offline, no network
uv run --group eda jupyter lab notebooks/01-pnoa-catastro-eda.ipynb  # the measurement
```

The `eda` dependency group is optional: a plain `uv sync` installs none of it.

## Who runs the measurement

The IGN, CNIG and Catastro domains are deliberately **not** in the agent sandbox
allowlist, so the measurement is run by a person on their own machine. An agent
can run the selftest and the notebook checker
(`python notebooks/eda_helpers.py --check-notebook <path>`), both offline.

## Where outputs go

Raw responses, `manifest.csv` (one line per request: UTC timestamp, URL, status,
bytes, MD5, elapsed time, error) and `extent.json` are written under
`data/interim/exp-001/`, which is git-ignored. The manifest is the audit trail:
a figure without a manifest line is not a measurement. The small derived tables
are displayed in the notebook and survive in its committed outputs.

## The provider is data

`PROVIDERS` in `eda_helpers.py` is the only place that names a host, a layer or
a vector attribute. Covering another country means adding an entry there.
