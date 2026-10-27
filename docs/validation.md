# Validation record

This file distinguishes tests that were actually run from configuration that is supplied.

- Local Python 3.9: 25 unit/integration tests passed, including live HTTP endpoints.
- Browser: UI loaded in Chrome; Russian discount search selected the expected function;
  incoming reference evidence displayed three callers and linked Markdown sections.
- Reproducibility: `scripts/evaluate.py` generated the checked-in metrics and error cases.
- Workflow: JSON structure and node/edge configuration validation passed.
- Self-analysis: RepoRadar successfully indexed its own source with no parsing warnings.

- Docker: image built successfully with Python 3.12; the container healthcheck passed.
- n8n 2.0.0: the exported workflow imported and executed through the real n8n CLI.
  The final node returned status `indexed`, 12 symbols, 10 references and 10 document
  sections. See `workflows/verified-output.json` for the captured summary.
- n8n error path: with the test service stopped, retries completed and the workflow
  reached `Explain scan failure` with status `failed`.
- SQL: all three analytical queries executed; reverse traversal returned the three
  expected callers of `discount`.
- Hosted CI: [run 40496193691](https://github.com/aliyushakham/reporadar/actions/runs/40496193691)
  passed all jobs: Python 3.9, 3.12 and 3.13 unit/integration tests, deterministic
  retrieval evaluation, workflow validation, package installation and Docker smoke test.
  Ubuntu 22.04 is pinned to retain Python 3.9 availability.

Validated on 2026-10-27. The fixtures are small and authored for this project; these
checks are not a claim of production readiness or broad retrieval accuracy.
