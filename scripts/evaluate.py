"""Reproduce retrieval metrics; evaluation fixture is separate from the demo corpus."""
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from reporadar.analyzer import analyze
from reporadar.search import SearchIndex


def metrics(ranked, relevant, k=5):
    relevant = set(relevant)
    top = ranked[:k]
    hits = [i + 1 for i, value in enumerate(top) if value in relevant]
    dcg = sum(1 / math.log2(rank + 1) for rank in hits)
    ideal = sum(1 / math.log2(i + 2) for i in range(min(k, len(relevant))))
    return {'recall@5': len(hits)/len(relevant),
            'mrr@5': 1/hits[0] if hits else 0,
            'ndcg@5': dcg/ideal if ideal else 0}


def main():
    queries = [json.loads(line) for line in (ROOT/'benchmarks/queries.jsonl').read_text().splitlines()]
    report = {'scope': 'Small author-labeled synthetic fixtures. No external generalization claim.',
              'methods': {}, 'errors': []}
    for split, corpus in [('development', ROOT/'examples/shop'), ('evaluation', ROOT/'benchmarks/corpus')]:
        index = SearchIndex(analyze(corpus))
        known = {r['id'] for r in index.records}
        selected = [q for q in queries if q['split']==split]
        for q in selected:
            if not set(q['relevant']) <= known:
                raise ValueError('Invalid gold IDs: '+str(set(q['relevant'])-known))
        report['methods'][split] = {}
        for method in ['identifier', 'bm25', 'hybrid']:
            scores = []
            for q in selected:
                results = index.search(q['query'], limit=5, method=method)
                ranked = [r['id'] for r in results]
                score = metrics(ranked, q['relevant'])
                scores.append(score)
                if score['mrr@5'] < 1:
                    report['errors'].append(dict(split=split, method=method, query=q['query'],
                        relevant=q['relevant'], retrieved=ranked))
            report['methods'][split][method] = dict(queries=len(selected), **{
                key: round(sum(s[key] for s in scores)/len(scores),4) for key in scores[0]})
    (ROOT/'benchmarks/results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(report['methods'], indent=2))

if __name__ == '__main__':
    main()
