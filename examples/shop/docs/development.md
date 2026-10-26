# Developer guide

## Changing delivery policy

Review `shipping` when changing the delivery fee or the free-shipping threshold.
Use RepoRadar's incoming references to inspect the affected order pipeline.

## Example request

```python
# This is a comment in a code block, not a Markdown heading.
submit_order({"items": [], "token": "demo"}, {})
```

## Limits

This fixture provides explicit imports and direct calls. Real systems also contain
dynamic dispatch, decorators, monkey-patching and dependency injection, which cannot
be reconstructed completely by this static analyzer.
