import sys
import unittest
from pathlib import Path

EXPERIMENT = Path(__file__).resolve().parents[1] / 'experimental/english-powerset'
sys.path.insert(0, str(EXPERIMENT))
from analyze import contrasts, outcome
from design import read
from features import features


class PowersetAnalysis(unittest.TestCase):
    def test_complete_pair_and_quartet_denominators_with_one_missing_cell(self):
        p = read(EXPERIMENT / 'protocol.json')
        data = {}
        for seed in p['seeds']:
            for mask in range(4):
                if seed == p['seeds'][2] and mask == 3:
                    continue
                x, y = mask & 1, (mask >> 1) & 1
                m = features('Example reply.')
                m['words'] = 2 + 3*x + 5*y + 8*x*y
                data[mask, seed] = {'metrics': m, 'bigrams': set()}
        effects, interactions, _ = contrasts(p, data)
        first = next(r for r in effects if r['field'] == 'ThresholdField' and r['measure'] == 'words')
        pair = next(r for r in interactions if r['first'] == 'ThresholdField'
                    and r['second'] == 'GentleField' and r['measure'] == 'words')
        self.assertEqual((first['matched_sets'], first['delta']), (5, 6.2))
        self.assertEqual((pair['matched_sets'], pair['delta']), (2, 8))
        self.assertIsNone(pair['delta_s303'])

    def test_length_refusal_missing_and_other_model_are_separate(self):
        def record(finish='stop', model='snapshot', refusal=None):
            return {'response': {'status_code': 200, 'body': {'model': model, 'choices': [
                {'finish_reason': finish, 'message': {'content': 'Partial text', 'refusal': refusal}}]}}}
        self.assertEqual(outcome(None, 'snapshot')[0], 'missing')
        self.assertEqual(outcome(record('length'), 'snapshot')[0], 'truncated')
        self.assertEqual(outcome(record(refusal='refusal'), 'snapshot')[0], 'refusal')
        self.assertEqual(outcome(record(model='other'), 'snapshot')[0], 'model_mismatch')
        self.assertEqual(outcome(record(), 'snapshot')[0], 'completed')

    def test_an_emotion_question_is_a_mention_without_a_declarative_attribution(self):
        a = features('Were you embarrassed when they laughed?')
        b = features('You felt embarrassed.')
        self.assertEqual((a['question'], a['emotion_word'], a['direct_attribution']), (1, 1, 0))
        self.assertEqual((b['question'], b['emotion_word'], b['direct_attribution']), (0, 1, 1))
