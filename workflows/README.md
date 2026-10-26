# n8n: repository indexing workflow

`reporadar-index.json` is an importable workflow with manual and webhook triggers:

```text
Manual / webhook → Index repository ─success→ Fetch snapshot → Build summary
                                  └─failure→ Explain failure
```

RepoRadar persists the snapshot to SQLite before the scan endpoint returns. The
workflow reports symbol/reference/document counts and warnings. It sends no emails,
opens no PRs, and runs no target repository code.

## Compose setup

1. Run `docker compose --profile automation up --build`.
2. Open http://127.0.0.1:5678 and complete your local n8n account setup.
3. Import `workflows/reporadar-index.json` via the workflow editor's **Import from file**.
4. Execute manually and inspect the final summary and stored snapshot in RepoRadar.
5. To use the webhook, activate/publish the workflow and POST to its displayed URL.
   The default production path is `/webhook/reporadar-scan`.

```bash
curl -X POST http://127.0.0.1:5678/webhook/reporadar-scan \
  -H 'Content-Type: application/json' -d '{}'
```

The workflow's HTTP URL is `http://reporadar:8765` because both services share the
Compose network. If n8n runs in Docker but RepoRadar runs directly on the host,
use Docker host networking/addressing appropriate for your platform and update the
server's allowed host policy explicitly. The supplied workflow is tested/designed
for the Compose topology; do not replace the host with `localhost` inside a container.

## Error behavior

Index requests retry up to three times, waiting two seconds between tries. After the
last failure, the error branch returns a diagnostic object. This is not a delivery
queue or an exactly-once guarantee: a retry can create another snapshot if a response
was lost after persistence. Snapshot comparison is structural and still works.

The scan endpoint ignores external repository paths: callers can only re-index the
checkout chosen when the service starts. To analyze a different checkout in Docker,
mount it read-only and replace the service command with its container path.

## Validation levels

`python3 scripts/validate_workflow.py` checks JSON shape, references, HTTP configuration,
and the error branch. It does not execute n8n. Actual runtime verification is recorded
in [validation](../docs/validation.md). The pinned n8n image is 2.0.0; newer versions may
migrate node settings on import.

Reference: [n8n Docker installation](https://docs.n8n.io/hosting/installation/docker/),
[HTTP Request node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.httprequest/).
