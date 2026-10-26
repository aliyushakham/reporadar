import json
import tempfile
import unittest
from pathlib import Path
from reporadar.analyzer import analyze, markdown_sections
from reporadar.graph import impact, compare
from reporadar.search import SearchIndex
from reporadar.storage import Store


class RepositoryTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, text):
        p = self.root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding='utf-8')
        return p

    def test_aliases_relative_imports_and_no_execution(self):
        self.write('pkg/__init__.py', '')
        self.write('pkg/pricing.py', 'def price():\n    return 42\n')
        self.write('pkg/api.py', 'from .pricing import price as quote\nimport pkg.pricing as p\ndef run():\n    return quote() + p.price()\nraise RuntimeError("must not run")\n')
        result = analyze(self.root)
        self.assertEqual(len(result['edges']), 2)
        self.assertEqual({e['target'] for e in result['edges']}, {'pkg/pricing.py::price'})

    def test_unknown_receiver_does_not_guess_by_method_name(self):
        self.write('a.py', 'def save():\n    pass\ndef run(client):\n    client.save()\n')
        result = analyze(self.root)
        self.assertEqual(result['edges'], [])
        self.assertEqual(len(result['unresolved']), 1)

    def test_local_shadowing_is_unresolved(self):
        self.write('a.py', 'def price():\n    return 1\ndef run(price):\n    return price()\n')
        self.assertEqual(analyze(self.root)['edges'], [])

    def test_nested_scope_and_recursive_cycle(self):
        self.write('a.py', 'def first():\n    second()\ndef second():\n    first()\ndef outer():\n    def helper():\n        return 1\n    return helper()\n')
        result = analyze(self.root)
        affected = impact(result, 'a.py::first')['affected']
        self.assertEqual([x['symbol']['id'] for x in affected], ['a.py::second'])
        # Nested local definitions should be resolved, unlike unknown local values.
        self.assertIn(('a.py::outer', 'a.py::outer.helper'), [(e['source'],e['target']) for e in result['edges']])

    def test_direct_receiver(self):
        self.write('a.py', 'class Service:\n    def save(self):\n        pass\n    def run(self):\n        self.save()\n')
        self.assertEqual(analyze(self.root)['edges'][0]['target'], 'a.py::Service.save')

    def test_duplicate_names_in_different_modules(self):
        self.write('a.py', 'def save():\n    pass\n')
        self.write('b.py', 'def save():\n    pass\ndef run():\n    save()\n')
        self.assertEqual(analyze(self.root)['edges'][0]['target'], 'b.py::save')

    def test_src_layout(self):
        self.write('src/pkg/a.py', 'def f():\n    pass\n')
        self.write('src/pkg/b.py', 'from pkg.a import f\ndef run():\n    f()\n')
        self.assertEqual(analyze(self.root)['edges'][0]['target'], 'src/pkg/a.py::f')

    def test_parse_errors_and_oversized_files(self):
        self.write('bad.py', 'def invalid(:\n')
        self.write('huge.md', 'x' * 1_000_001)
        result = analyze(self.root)
        self.assertEqual(len(result['warnings']), 2)

    def test_symlink_is_not_followed(self):
        outside = self.write('a.py', 'def f():\n    pass\n')
        (self.root / 'linked.py').symlink_to(outside)
        self.assertEqual(len(analyze(self.root)['symbols']), 1)

    def test_fenced_heading_is_not_section(self):
        content = '# One\n```python\n# not a heading\n```\n## Two\ntext\n'
        sections = markdown_sections('README.md', content)
        self.assertEqual([s['title'] for s in sections], ['One', 'Two'])
        self.assertEqual([s['line'] for s in sections], [1, 5])
        self.assertEqual(sections[0]['end_line'], 4)

    def test_bm25_russian_glossary_and_empty(self):
        self.write('price.py', 'def discount(total):\n    """Apply loyalty discount."""\n    return total * 0.9\ndef ship():\n    """Shipping delivery."""\n    return 0\n')
        search = SearchIndex(analyze(self.root))
        self.assertEqual(search.search('Где рассчитывается скидка?')[0]['id'], 'price.py::discount')
        self.assertEqual(search.search('zxqj_unfindable'), [])
        self.assertEqual(search.search(''), [])

    def test_snapshot_roundtrip_and_sql_integrity(self):
        self.write('a.py', 'def f():\n    return 1\ndef g():\n    return f()\n')
        snapshot = analyze(self.root)
        store = Store(self.root / 'data.sqlite')
        run = store.save(snapshot)
        self.assertEqual(store.load(run), snapshot)
        with store.connect() as db:
            self.assertEqual(db.execute('PRAGMA foreign_key_check').fetchall(), [])
            self.assertEqual(db.execute('SELECT count(*) FROM edges').fetchone()[0], 1)
        self.assertEqual(len(store.runs()), 1)
        with self.assertRaises(ValueError):
            store.load(999)

    def test_change_impact_and_removed_symbol(self):
        self.write('a.py', 'def f():\n    return 1\ndef g():\n    return f()\n')
        old = analyze(self.root)
        self.write('a.py', 'def f():\n    return 2\ndef g():\n    return f()\n')
        new = analyze(self.root)
        changes = compare(old, new)['changes']
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0]['status'], 'modified')
        self.assertEqual(changes[0]['impact']['affected'][0]['symbol']['name'], 'g')
        self.write('a.py', 'def g():\n    return 2\n')
        deleted = compare(new, analyze(self.root))['changes']
        self.assertEqual(next(c for c in deleted if c['status']=='removed')['previous_callers'][0]['symbol']['name'], 'g')

    def test_whitespace_change_is_not_code_change(self):
        self.write('a.py', 'def f():\n    return 1\n')
        old = analyze(self.root)
        self.write('a.py', '\n\ndef f():\n    # comment\n    return 1\n')
        self.assertEqual(compare(old, analyze(self.root))['count'], 0)

    def test_depth_limit(self):
        self.write('a.py', 'def a():\n    b()\ndef b():\n    c()\ndef c():\n    pass\n')
        result = impact(analyze(self.root), 'a.py::c', depth=1)
        self.assertEqual([a['symbol']['name'] for a in result['affected']], ['b'])
