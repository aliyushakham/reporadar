import unittest
from scripts.evaluate import metrics


class MetricsTest(unittest.TestCase):
    def test_multiple_relevant_results(self):
        score = metrics(['x', 'a', 'b'], ['a', 'b'])
        self.assertEqual(score['recall@5'], 1)
        self.assertEqual(score['mrr@5'], 0.5)
        self.assertGreater(score['ndcg@5'], 0.6)
        self.assertLess(score['ndcg@5'], 1)

    def test_cutoff_and_no_match(self):
        score = metrics(['a','b','c','d','e','gold'], ['gold'])
        self.assertEqual(score, {'recall@5':0, 'mrr@5':0, 'ndcg@5':0})

    def test_ideal_ranking(self):
        self.assertEqual(metrics(['a','b'], ['a','b']), {'recall@5':1, 'mrr@5':1, 'ndcg@5':1})
