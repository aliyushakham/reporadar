# Validation record

This file distinguishes tests that were actually run from configuration that is supplied.

- Local Python 3.9: 22 unit/integration tests passed, including live HTTP endpoints.
- Browser: UI loaded in Chrome; Russian discount search selected the expected function;
  incoming reference evidence displayed three callers and linked Markdown sections.
- Reproducibility: `scripts/evaluate.py` generated the checked-in metrics and error cases.
- Workflow: JSON structure and node/edge configuration validation passed.
- Self-analysis: RepoRadar successfully indexed its own source with no parsing warnings.

Docker, n8n execution and hosted CI verification are recorded below as they complete.
