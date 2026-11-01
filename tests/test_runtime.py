import hashlib
import http.client
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'runtime'))
from field_observatory.prompts import catalog, compile_prompt
from field_observatory.provider import Session, request_body
from field_observatory.server import make_server
from field_observatory.signals import verify_samples


class PromptsAndEvidence(unittest.TestCase):
    def test_public_pack_has_twelve_bilingual_cards_and_eight_presets(self):
        pack, presets = catalog()
        self.assertEqual(len(pack['fields']), 12)
        self.assertEqual(len(presets), 8)
        for card in pack['fields']:
            self.assertEqual(card['status'], 'proposed_operational_interpretation')
            self.assertNotIn('source', card)
            self.assertEqual(set(card['locales']), {'en', 'ja'})

    def test_plain_and_structured_include_the_same_moves(self):
        pack, presets = catalog()
        for language in ('en', 'ja'):
            for preset, ids in presets.items():
                plain = compile_prompt(preset, 'plain', language=language)['instructions']
                structured = compile_prompt(preset, 'structured', language=language)['instructions']
                for f in pack['fields']:
                    local = f['locales'][language]
                    for move in [local['when'], *local['moves']]:
                        self.assertEqual(move in plain, f['id'] in ids)
                        self.assertEqual(move in structured, f['id'] in ids)

    def test_english_default_and_japanese_are_distinct_exact_exports(self):
        en = compile_prompt('all-fields')
        ja = compile_prompt('all-fields', language='ja')
        self.assertEqual(en['language'], 'en')
        self.assertEqual(ja['language'], 'ja')
        self.assertEqual(en['fields'], ja['fields'])
        self.assertTrue(en['instructions'].startswith('Respond naturally'))
        self.assertTrue(ja['instructions'].startswith('相手が使う言語'))
        self.assertNotEqual(en['instructions_sha256'], ja['instructions_sha256'])

    def test_single_and_custom_order_are_preserved(self):
        single = compile_prompt(field_ids=['HeartField'])
        self.assertEqual(single['fields'], ['HeartField'])
        ids = ['TranslationDrive', 'HeartField', 'GroundField']
        a = compile_prompt(field_ids=ids)
        b = compile_prompt(field_ids=list(reversed(ids)))
        self.assertEqual(a['fields'], ids)
        self.assertEqual(a['preset'], 'custom')
        self.assertNotEqual(a['instructions_sha256'], b['instructions_sha256'])
        for earlier, later in zip(ids, ids[1:]):
            self.assertLess(a['instructions'].index(earlier), a['instructions'].index(later))

    def test_invalid_and_empty_custom_combinations_fail_closed(self):
        for fields in ([], ['MissingField'], ['HeartField', 'HeartField'], 'HeartField', [None], [{}]):
            with self.subTest(fields=fields), self.assertRaises(ValueError): compile_prompt(field_ids=fields)
        for language in ('fr', '', None):
            with self.assertRaises(ValueError): compile_prompt(language=language)
        with self.assertRaises(ValueError): compile_prompt('custom')
        self.assertEqual(compile_prompt('custom', 'baseline', field_ids=[])['fields'], [])

    def test_baseline_does_not_depend_on_preset(self):
        a = compile_prompt('quiet-dialogue', 'baseline')
        b = compile_prompt('all-fields', 'baseline')
        self.assertEqual(a['instructions'], b['instructions'])
        self.assertEqual(a['fields'], [])
        self.assertEqual(a['instructions_sha256'], hashlib.sha256(a['instructions'].encode()).hexdigest())

    def test_unknown_modes_and_presets_are_rejected(self):
        for preset, mode in [('missing', 'plain'), ('quiet-dialogue', 'missing')]:
            with self.assertRaises(ValueError): compile_prompt(preset, mode)

    def test_public_numeric_parameters_reproduce_original_samples(self):
        report = verify_samples(portable=True)
        self.assertEqual((report['verified_samples'], report['steps_per_sample']), (5, 384))
        self.assertLessEqual(report['max_absolute_difference'], report['absolute_tolerance'])

    def test_historical_missing_slot_is_not_filled_or_relabeled(self):
        pilot = json.loads((ROOT / 'data/api-pilot.json').read_text())
        responses = [r for c in pilot['cases'] for r in c['responses'].values()]
        self.assertEqual(sum(bool(r['reply']) for r in responses), 17)
        missing = next(c for c in pilot['cases'] if c['id'] == 'c04')['responses']['baseline']
        self.assertEqual(missing['status'], 'transport_or_decode_error')
        self.assertEqual(missing['reply'], '')
        self.assertTrue(pilot['not_an_evaluation_of_public_prompts'])

    def test_forced_label_and_uncertain_reply_both_survive_projection(self):
        data = json.loads((ROOT / 'data/dialogue.json').read_text())
        self.assertEqual(sum(len(rs) for c in data['cases'] for rs in c['responses'].values()), 108)
        case = next(c for c in data['cases'] if c['id'] == 'c10')
        self.assertEqual(case['turns'][0]['reference'], 'U')
        self.assertEqual(case['responses']['immediate'][0]['label'], 'B')
        self.assertIn('審査結果が出たら', case['responses']['immediate'][0]['reply'])

    def test_public_data_manifest_covers_all_data_files(self):
        manifest = json.loads((ROOT / 'data/manifest.json').read_text())
        expected = {str(p.relative_to(ROOT)) for p in (ROOT / 'data').glob('*.json') if p.name != 'manifest.json'}
        self.assertEqual(set(manifest['files']), expected)
        for name, sha in manifest['files'].items():
            self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), sha)


class ExecutionBoundaries(unittest.TestCase):
    def setUp(self):
        self.key = 'synthetic-credential-only-for-unit-test'
        self.env = patch.dict(os.environ, {'OPENAI_API_KEY': self.key})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.sent = []

    def send(self, body, key):
        self.sent.append(body)
        self.assertEqual(key, self.key)
        return {'status': 'completed', 'reply': '受け取りました。', 'usage': None}

    def test_request_is_stateless_and_bounded(self):
        body, _ = request_body('hello', 'quiet-dialogue', 'structured')
        self.assertFalse(body['store'])
        self.assertEqual(body['max_output_tokens'], 600)
        self.assertNotIn('previous_response_id', body)
        self.assertNotIn('tools', body)

    def test_custom_language_and_order_reach_dispatch_and_receipt(self):
        ids = ['ShieldField', 'TranslationDrive']
        with tempfile.TemporaryDirectory() as tmp:
            result = Session(enabled=True, records=tmp, send=self.send).run('hello', 'custom', 'structured', language='ja', field_ids=ids)
            saved = json.loads((Path(tmp) / result['run_id'] / 'dispatch.json').read_text())
            expected = compile_prompt('custom', language='ja', field_ids=ids)
            self.assertEqual(self.sent[0]['instructions'], expected['instructions'])
            self.assertEqual(saved['prompt']['language'], 'ja')
            self.assertEqual(saved['prompt']['fields'], ids)
            self.assertEqual(result['prompt']['instructions_sha256'], expected['instructions_sha256'])

    def test_disabled_mode_never_calls_transport(self):
        session = Session(send=self.send)
        with self.assertRaises(ValueError): session.run('hello', 'quiet-dialogue', 'plain')
        self.assertEqual(self.sent, [])

    def test_records_cannot_be_written_into_served_public_assets(self):
        for path in (ROOT, ROOT / 'app/runs', ROOT / 'data/runs', ROOT / 'prompts/runs'):
            with self.assertRaises(ValueError): Session(records=path)

    def test_budget_stops_before_a_second_request(self):
        session = Session(enabled=True, limit=1, send=self.send)
        session.run('hello', 'quiet-dialogue', 'plain')
        with self.assertRaises(ValueError): session.run('hello', 'quiet-dialogue', 'plain')
        self.assertEqual(len(self.sent), 1)

    def test_failed_request_is_counted_and_not_retried(self):
        def failed(body, key):
            self.sent.append(body)
            return {'status': 'transport_or_decode_error', 'reply': ''}
        session = Session(enabled=True, limit=3, send=failed)
        result = session.run('hello', 'quiet-dialogue', 'plain')
        self.assertEqual(result['status'], 'transport_or_decode_error')
        with self.assertRaises(ValueError): session.run('again', 'quiet-dialogue', 'plain')
        self.assertEqual(len(self.sent), 1)
        self.assertEqual(session.attempted, 1)

    def test_incomplete_response_is_retained_and_stops_session(self):
        session = Session(enabled=True, send=lambda *_: {'status': 'incomplete', 'reply': 'unfinished'})
        result = session.run('hello', 'quiet-dialogue', 'plain')
        self.assertEqual(result['reply'], 'unfinished')
        self.assertTrue(session.stopped)

    def test_credential_input_never_dispatches_or_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            session = Session(enabled=True, records=tmp, send=self.send)
            with self.assertRaises(ValueError): session.run(self.key, 'quiet-dialogue', 'plain')
            self.assertEqual(list(Path(tmp).iterdir()), [])
        self.assertEqual(self.sent, [])

    def test_credential_echo_is_removed_before_persistence(self):
        with tempfile.TemporaryDirectory() as tmp:
            session = Session(enabled=True, records=tmp, send=lambda *_: {'status': 'completed', 'reply': self.key})
            result = session.run('hello', 'quiet-dialogue', 'plain')
            self.assertEqual(result['status'], 'credential_echo_blocked')
            self.assertNotIn(self.key, json.dumps(result))
            for file in Path(tmp).rglob('*.json'):
                self.assertNotIn(self.key, file.read_text())
                self.assertEqual(file.stat().st_mode & 0o777, 0o600)

    def test_invalid_requests_do_not_consume_budget(self):
        session = Session(enabled=True, send=self.send)
        for value in ['', 'a' * 4001, None, 123]:
            with self.assertRaises(ValueError): session.run(value, 'quiet-dialogue', 'plain')
        self.assertEqual(session.attempted, 0)

    def test_receipt_binds_all_saved_request_and_result_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = Session(enabled=True, records=tmp, send=self.send).run('hello', 'quiet-dialogue', 'plain')
            directory = Path(tmp) / result['run_id']
            receipt = json.loads((directory / 'receipt.json').read_text())
            self.assertEqual(set(receipt['files']), {'request.json', 'dispatch.json', 'result.json'})
            for name, sha in receipt['files'].items():
                self.assertEqual(hashlib.sha256((directory / name).read_bytes()).hexdigest(), sha)


class ServerBoundary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = make_server(Session(), 0)
        cls.port = cls.server.server_port
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.thread.join()

    def call(self, method, path, body=None, headers=None):
        conn = http.client.HTTPConnection('127.0.0.1', self.port, timeout=5)
        try:
            conn.request(method, path, body=body, headers=headers or {})
            response = conn.getresponse()
            return response.status, response.read()
        finally: conn.close()

    def test_only_public_routes_are_served(self):
        self.assertEqual(self.call('GET', '/')[0], 200)
        for path in ('/.runs/request.json', '/.git/config', '/../README.md', '/runtime/field_observatory/provider.py'):
            self.assertEqual(self.call('GET', path)[0], 404)

    def test_foreign_host_and_origin_are_rejected(self):
        self.assertEqual(self.call('GET', '/', headers={'Host': 'untrusted.example'})[0], 403)
        self.assertEqual(self.call('POST', '/api/run', '{}', {'Origin': 'https://untrusted.example'})[0], 403)

    def test_preview_requires_nonce_but_never_requires_a_key(self):
        _, raw = self.call('GET', '/api/session')
        nonce = json.loads(raw)['nonce']
        headers = {'Origin': f'http://127.0.0.1:{self.port}', 'Content-Type': 'application/json'}
        self.assertEqual(self.call('POST', '/api/preview', '{}', headers)[0], 403)
        headers['X-Observatory-Nonce'] = nonce
        with patch.dict(os.environ, {}, clear=True):
            status, raw = self.call('POST', '/api/preview', '{}', headers)
        self.assertEqual(status, 200)
        self.assertIn('instructions', json.loads(raw))
        self.assertEqual(self.call('POST', '/api/run', '{"input":"hello"}', headers)[0], 400)

    def test_preview_accepts_bilingual_custom_fields_and_rejects_invalid_language(self):
        _, raw = self.call('GET', '/api/session')
        headers = {'Origin': f'http://127.0.0.1:{self.port}', 'Content-Type': 'application/json', 'X-Observatory-Nonce': json.loads(raw)['nonce']}
        payload = {'preset': 'custom', 'fields': ['HeartField'], 'language': 'ja'}
        status, raw = self.call('POST', '/api/preview', json.dumps(payload), headers)
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(raw)['fields'], ['HeartField'])
        self.assertEqual(json.loads(raw)['language'], 'ja')
        payload['language'] = 'unsupported'
        self.assertEqual(self.call('POST', '/api/preview', json.dumps(payload), headers)[0], 400)


if __name__ == '__main__':
    unittest.main()
