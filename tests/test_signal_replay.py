import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'runtime'))
from field_observatory.signals import compare_portable_trace


class PortableReplay(unittest.TestCase):
    reference = {'id': 'sample', 'seed': 1000, 'label': 'Sample',
                 'latent': [0.0], 'observation': [0.35], 'memory': [0.2]}

    def compare(self, **changes):
        return compare_portable_trace({**self.reference, **changes}, self.reference, [0, 0.35])

    def test_accepts_roundoff_but_rejects_different_or_nonfinite_values(self):
        adjacent = math.nextafter(0.35, 1.0)
        self.assertEqual(self.compare(observation=[adjacent]), adjacent - 0.35)
        for values in ([0.36], [math.nan], [math.inf], []):
            with self.subTest(values=values), self.assertRaises(ValueError):
                self.compare(observation=values)

    def test_even_one_ulp_cannot_change_a_decision_or_null_truth(self):
        with self.assertRaisesRegex(ValueError, 'decision'):
            self.compare(observation=[math.nextafter(0.35, 0.0)])
        with self.assertRaisesRegex(ValueError, 'truth'):
            self.compare(latent=[math.nextafter(0.0, 1.0)])
