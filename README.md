<div align="center">

# ◉ RepoRadar

### Understand a Python codebase. Follow the evidence.

AST-powered repository maps · Code & documentation retrieval · Change impact

[![Tests](https://github.com/aliyushakham/reporadar/actions/workflows/ci.yml/badge.svg)](https://github.com/aliyushakham/reporadar/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.9%2B-7353d6)
![Dependencies](https://img.shields.io/badge/runtime_dependencies-0-3d9d83)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

[Quick start](#quick-start) · [По-русски](docs/README.ru.md) · [Architecture](docs/architecture.md) · [Evaluation](docs/evaluation.md) · [n8n](workflows/README.md)

</div>

RepoRadar helps you explore an unfamiliar Python repository and review the potential
impact of a change. Search for a concept, inspect the original source, trace callers
and callees, and find related documentation — with file paths and line numbers.

**Example:** “Где рассчитывается скидка?” → `discount` → incoming references through
`quote`, `checkout`, and `submit_order` → the “Price calculation” documentation section.

The tool analyzes files without importing or executing the target project. It runs
locally, needs no API key, and makes no external inference requests.

## Quick start

```bash
git clone https://github.com/aliyushakham/reporadar.git
cd reporadar
python3 -m reporadar serve examples/shop
```

Open **http://127.0.0.1:8765**. Python 3.9+ is required; the application has no runtime
dependencies. Syntax support follows the interpreter you use: use a sufficiently
recent Python for repositories with newer syntax.

Explore your own local checkout:

```bash
python3 -m reporadar --db .reporadar/my-project.sqlite serve /path/to/project
```

Optional installation: `python3 -m pip install .` exposes the `reporadar` command.

## What works

| Capability | Implementation |
|---|---|
| Repository map | Python AST, source spans, import aliases, direct and lexical call references |
| Evidence search | Identifier baseline, BM25, BM25 + identifier boost + explicit Russian glossary |
| Impact analysis | Cycle-safe reverse/forward graph traversal with shortest evidence paths |
| Documentation | Markdown sections with heading and fenced-code awareness; linked by retrieval |
| Change review | Structural AST fingerprints, added/removed/modified symbols, previous/current callers |
| History | Atomic SQLite snapshots plus normalized symbols, edges and document tables |
| Automation | JSON CLI, local HTTP API, importable n8n workflow with retry/error branch |
| Delivery | Local UI, Dockerfile, Compose, CI and reproducible evaluation |

### A 2-minute demo

1. Launch the included MiniShop example.
2. Click **Расчёт скидки**; inspect source lines and affected callers.
3. Click **Price calculation** to read the original Markdown section.
4. Change `total // 10` to `total // 5` in `examples/shop/shop/pricing.py`.
5. Click **Re-index**, open **Snapshot history**, compare the earlier snapshot to current.
6. Inspect the changed symbol, its callers and documentation review suggestions.
7. Restore the example after your experiment.

The change comparison is a review aid. It does **not** claim a related document is
incorrect, nor does a static call edge prove runtime execution or data flow.

## CLI

```bash
python3 -m reporadar scan examples/shop
python3 -m reporadar search 'Где рассчитывается скидка?'
python3 -m reporadar search 'shipping' --method bm25
python3 -m reporadar impact 'shop/pricing.py::discount'
python3 -m reporadar impact 'shop/checkout.py::checkout' --direction callees
python3 -m reporadar runs
# Use actual IDs printed by `runs`:
python3 -m reporadar compare 1 2
python3 -m reporadar scan examples/shop --output .reporadar/snapshot.json
```

`--db` is a global option and goes **before** the subcommand. CLI output is JSON.
Exports contain source text and the local repository path; review before sharing.

## Evaluation

A small **author-labeled synthetic benchmark** separates the MiniShop development
fixture from a library-domain evaluation fixture. Search configuration is fixed;
there is no model training. It is a regression/reproducibility exercise, not a
large-scale benchmark or an externally validated generalization claim.

| Retrieval method | Eval queries | Recall@5 | MRR@5 | nDCG@5 |
|---|---:|---:|---:|---:|
| Identifier tokens | 14 | 0.3571 | 0.3036 | 0.3165 |
| BM25 | 14 | 0.7857 | 0.7500 | 0.7594 |
| BM25 + identifier boost + glossary | 14 | 0.8571 | 0.8571 | 0.8571 |

```bash
python3 -m unittest discover -s tests -v
python3 scripts/evaluate.py
python3 scripts/validate_workflow.py
```

[Queries and labels](benchmarks/queries.jsonl), [raw results and failures](benchmarks/results.json),
and [evaluation design](docs/evaluation.md) are versioned. Metrics include code and
documentation in the same retrieval pool. Two evaluation queries fail even with the
glossary; see the error analysis. We do not equate this lexical approach with a
trained multilingual semantic model.

## Docker and n8n

```bash
docker compose up --build
# Or include the automation service:
docker compose --profile automation up --build
```

If the Python demo is already running, stop it before starting Compose on port 8765.
The UI is at http://127.0.0.1:8765; n8n is at http://127.0.0.1:5678.
Import [the workflow](workflows/reporadar-index.json), then execute it manually.
See [setup and verification](workflows/README.md).

## Project layout

```text
reporadar/       AST analysis, retrieval, graph traversal, SQLite, CLI, API, UI
examples/shop/  Small executable-shaped exploration fixture (never executed by the tool)
benchmarks/     Separate evaluation corpus, query labels and recorded retrieval errors
tests/          AST, graph, retrieval, storage and HTTP integration tests
sql/            Parameterized analytical SQL and recursive caller traversal
workflows/      Importable n8n automation and setup instructions
docs/           Architecture, limitations, evaluation, Russian guide, interview notes
scripts/        Reproducible evaluation and workflow validation
```

## Scope and limitations

- Python source and Markdown only. No PDF/OCR, JavaScript parsing or GitHub cloning endpoint.
- Direct explicit imports and lexical calls are supported; wildcard imports, re-export
  chains, inheritance dispatch, instance type inference, decorators, monkey-patching,
  callbacks and runtime dependency injection are not fully resolved.
- Built-in/external calls remain unresolved unless their definitions are in the index.
  An unresolved call is not necessarily a defect.
- Default-argument/decorator calls and module-level execution are not modeled as function
  call edges. Syntax errors are surfaced as warnings, not silently discarded.
- Query expansion is a small inspectable Russian-to-English glossary. Unseen concepts
  and paraphrases can fail. No LLM answers or learned embeddings are claimed.
- Snapshot IDs are local; comparisons require the same repository path. Renames appear
  as removal plus addition. Comment-only edits do not change AST fingerprints.
- Source files over 1 MB are skipped; repositories over 5,000 Python/Markdown files are
  rejected. Symlinks and common generated/hidden directories are skipped. The UI shows
  up to 100 graph nodes; search focuses a smaller graph. Search is linear in index size.
- This is a local single-user development tool, **not** a hardened multi-tenant server.
  Keep ports local. SQLite snapshots contain source text. See [security](SECURITY.md).

## Next experiments

Evaluate on independently annotated real repositories, add learned retrieval with an
ablation against these baselines, and extend conservative resolution of re-exports.
These are future work, not features of the current release.

## License

MIT. Included fixtures and benchmark labels are original examples distributed under
the same license. Analyzed third-party repositories keep their original licenses.
