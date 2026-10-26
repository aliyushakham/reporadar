# Local-use security model

RepoRadar parses source and never imports or executes the analyzed project. Symlinks
are not followed. Files are size-limited, file counts are capped, source text is escaped
in the browser, and HTTP routes cannot select arbitrary filesystem paths.

This does not make parsing adversarial files resource-safe: extreme AST nesting,
large syntax trees or many files may exhaust resources. Inspect trusted local checkouts.

SQLite snapshots and JSON exports contain source code. Store them privately. The
application is intended for one local user and has no authentication. Keep published
ports on 127.0.0.1; do not expose the service publicly. Allowed HTTP hosts are localhost,
127.0.0.1 and the Compose service name reporadar. Browser cross-origin requests are
rejected, but this is not a substitute for authentication on an untrusted network.

Do not put secrets in the analyzed demonstration repository. No tokens are required
by RepoRadar or its n8n workflow. The workflow targets only the configured repository.
