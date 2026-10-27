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
- SQL: all three analytical queries executed; reverse traversal returned the three
  expected callers of `discount`.
- Hosted CI: the first upload exposed a YAML quoting error in the Docker smoke-test
  command; the command was changed to a YAML block scalar. The final run is checked
  before release.
