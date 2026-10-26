"""Reproducible lexical retrieval: BM25 + identifier evidence + optional glossary.

No learned embeddings or hidden API calls. Russian expansion is a small explicit
query glossary, not a general multilingual semantic model.
"""
import math
import re
from collections import Counter

GLOSSARY = {
    "скид": ["discount", "promotion"], "стоим": ["price", "total", "cost"],
    "цен": ["price", "cost"], "заказ": ["order", "checkout"],
    "достав": ["shipping", "delivery"], "оплат": ["payment", "charge"],
    "возврат": ["refund", "return"], "платеж": ["payment", "charge"],
    "налог": ["tax"], "запас": ["stock", "inventory"], "остат": ["stock", "inventory"],
    "товар": ["product", "item"], "клиент": ["customer", "client"],
    "пользоват": ["user", "customer"], "провер": ["validate", "check"],
    "сохран": ["save", "store"], "загруз": ["load", "read"],
    "отчет": ["report"], "отчёт": ["report"], "корзин": ["basket", "cart"],
    "настрой": ["config", "settings"], "уведом": ["notification", "notify"],
    "токен": ["token"], "авториз": ["auth", "authenticate"],
    "кеш": ["cache"], "кэш": ["cache"], "ошиб": ["error", "exception"],
}
STOP = set("the a an is are how what where does do to of in and for from with this which как где что это при для или на ли и в по из".split())


def tokens(text):
    text = re.sub(r"([a-zа-я])([A-ZА-Я])", r"\1 \2", text)
    return [t for t in re.findall(r"[^\W_]+", text.lower()) if t not in STOP and len(t) > 1]


def expand(query):
    terms = tokens(query)
    for term in list(terms):
        for prefix, values in GLOSSARY.items():
            if term.startswith(prefix):
                terms.extend(values)
    return list(dict.fromkeys(terms))


class SearchIndex:
    def __init__(self, snapshot):
        self.records = []
        for s in snapshot["symbols"]:
            self.records.append(dict(id=s["id"], kind="code", title=s["qualname"], path=s["path"],
                line=s["line"], end_line=s["end_line"], text=s["source"],
                searchable=f'{s["qualname"]} {s["signature"]} {s["docstring"]} {s["source"]}'))
        for d in snapshot["documents"]:
            self.records.append(dict(d, kind="document", searchable=d["title"] + " " + d["text"]))
        self.counts = [Counter(tokens(r["searchable"])) for r in self.records]
        self.lengths = [sum(c.values()) for c in self.counts]
        self.avg = sum(self.lengths) / max(1, len(self.lengths)) or 1
        self.df = Counter(t for c in self.counts for t in c)

    def search(self, query, limit=10, method="hybrid", kind=None):
        if method not in {"bm25", "hybrid", "identifier"}:
            raise ValueError("Unknown search method")
        q = expand(query) if method == "hybrid" else tokens(query)
        results = []
        for record, counts, length in zip(self.records, self.counts, self.lengths):
            if kind and record["kind"] != kind:
                continue
            score = 0.0
            matched = []
            for term in q:
                tf = counts[term]
                if tf:
                    idf = math.log(1 + (len(self.records) - self.df[term] + 0.5) / (self.df[term] + 0.5))
                    score += idf * tf * 2.5 / (tf + 1.5 * (0.25 + 0.75 * length / self.avg))
                    matched.append(term)
            title_terms = set(tokens(record["title"]))
            overlap = len(title_terms.intersection(q))
            if method == "identifier":
                score = float(overlap)
            elif method == "hybrid":
                score += 1.5 * overlap
            if score > 0:
                item = {k: v for k, v in record.items() if k != "searchable"}
                results.append(dict(item, score=round(score, 5), matched_terms=matched))
        return sorted(results, key=lambda r: (-r["score"], r["id"]))[:limit]


def related_documents(snapshot, symbol_id, limit=5):
    symbol = next((s for s in snapshot["symbols"] if s["id"] == symbol_id), None)
    if symbol is None:
        raise ValueError("Unknown symbol")
    return SearchIndex(snapshot).search(symbol["name"] + " " + symbol["docstring"], limit, kind="document")
