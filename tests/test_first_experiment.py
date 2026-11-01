import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'experimental/naming-hold/run.py'
spec = importlib.util.spec_from_file_location('naming_hold', SCRIPT)
experiment = importlib.util.module_from_spec(spec)
spec.loader.exec_module(experiment)


class NamingHold(unittest.TestCase):
    def test_frozen_requests_differ_only_in_instructions(self):
        with patch.dict(os.environ, {}, clear=True):
            _, previews = experiment.prepare()
        common, threshold = previews
        self.assertEqual(common['prompt']['fields'], [])
        self.assertEqual(threshold['prompt']['fields'], ['ThresholdField'])
        self.assertEqual(common['request']['model'], 'gpt-6-sol')
        self.assertEqual(common['prompt']['language'], 'ja')
        self.assertEqual(common['request'].keys(), threshold['request'].keys())
        changed = {k for k in common['request'] if common['request'][k] != threshold['request'][k]}
        self.assertEqual(changed, {'instructions'})

    def test_failed_first_slot_preserves_the_unattempted_slot_and_refuses_replay(self):
        calls = []
        def disconnect(body, _key):
            calls.append(body)
            return {'status': 'transport_or_decode_error', 'reply': ''}

        protocol, previews = experiment.prepare()
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {'OPENAI_API_KEY': 'fixture-only'}):
            directory = Path(tmp) / 'trial'
            slots = experiment.execute(protocol, previews, directory, send=disconnect)
            self.assertEqual([s['status'] for s in slots], ['transport_or_decode_error', 'not_attempted'])
            self.assertTrue((directory / 'slots.json').is_file())
            with self.assertRaises(FileExistsError):
                experiment.execute(protocol, previews, directory, send=disconnect)
        self.assertEqual(calls, [previews[0]['request']])
