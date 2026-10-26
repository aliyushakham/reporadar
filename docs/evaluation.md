# Evaluation protocol

## What the numbers mean

The checked-in corpus consists of original, author-written fixtures, not naturally
sampled production repositories. Development uses MiniShop (6 queries); evaluation
uses a separate library domain (14 queries). Labels were written by the same project
author, so independence and statistical power are limited. No training is performed.

The experiment compares identifier token overlap, BM25, and BM25 with an identifier
boost and Russian glossary. Search configuration is shared across both corpora. We
report all queries, including failures, and do not tune on the evaluation failures.

`python3 scripts/evaluate.py` regenerates `benchmarks/results.json`. CI checks that
re-running produces the same file. Source paths and labels are validated before scoring.

- Recall@5: number of relevant results in the first 5 divided by all labeled relevant results.
- MRR@5: reciprocal rank of the first relevant result, or zero if absent from the first 5.
- nDCG@5: binary relevance with log2 discount, normalized by the ideal first 5.
- Final values: macro averages across queries. No confidence or significance claim is made.

Evaluation results: identifier Recall@5 0.3571; BM25 0.7857; expanded/boosted BM25 0.8571.
These are fixture-specific results and must not be advertised as production accuracy.

## Error analysis

The expanded method still fails the Russian query about an overdue fine, because the
small glossary has no corresponding terms. It also fails the English paraphrase
“library member verified” because lexical retrieval does not connect those words to
“reader”, “authenticate”, and “token”. These failures motivate a future learned-retrieval
experiment. They are deliberately retained rather than patched into the glossary.

In MiniShop, discount terminology can retrieve a discount function when the intended
answer is the final quote. Function bodies and documentation repeat related concepts;
query understanding and graded relevance would improve the evaluation design.

## Structural checks

Tests exercise alias and relative imports, duplicate function names across modules,
local shadowing, nested definitions, direct receivers, src layouts, recursive cycles,
depth limits, syntax errors, file-size caps, symlinks and fenced Markdown headings.
They also verify change detection, deleted-symbol callers, SQL foreign keys and the
HTTP contract, including local-origin protections. Tests do not establish whole-language
static-analysis soundness.

## External validity: next study

Before making broad quality claims:
1. Select multiple independently maintained Python projects of varying size.
2. Have another annotator write realistic onboarding/change-review questions.
3. Split by repository, not by fragments from the same file.
4. Freeze hyperparameters before scoring the held-out repositories.
5. Compare BM25, trained/pretrained code-text embeddings, and reranking; measure latency.
6. Audit both false resolved edges and missed edges on annotated call sites.
7. Publish annotation guidelines, disagreements and per-query errors.

The present release intentionally makes none of those unperformed claims.
