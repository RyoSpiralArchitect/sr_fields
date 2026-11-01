import http.client
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'runtime'))
from field_observatory.provider import request_body, transport


class FakeResponse:
    def __init__(self, status, raw):
        self.status, self.raw, self.reads = status, raw, 0

    def read(self, limit):
        self.reads += 1
        return self.raw[:limit]


class FakeConnection:
    def __init__(self, response=None, error=None):
        self.response, self.error, self.requests, self.closed = response, error, [], False

    def request(self, *args, **kwargs):
        self.requests.append((args, kwargs))
        if self.error: raise self.error

    def getresponse(self): return self.response
    def close(self): self.closed = True


class ResponsesAdapter(unittest.TestCase):
    def call(self, status=200, value=None, raw=None, error=None):
        response = FakeResponse(status, raw if raw is not None else json.dumps(value).encode())
        connection = FakeConnection(response, error)
        body, _ = request_body('test', 'quiet-dialogue', 'plain')
        with patch('field_observatory.provider.http.client.HTTPSConnection', return_value=connection) as factory:
            result = transport(body, 'synthetic-adapter-credential')
        self.assertEqual(factory.call_args.args, ('api.openai.com',))
        self.assertEqual(len(connection.requests), 1)
        self.assertEqual(connection.requests[0][0], ('POST', '/v1/responses'))
        self.assertTrue(connection.closed)
        return result, response

    def test_output_text_is_extracted_without_reasoning_items(self):
        result, _ = self.call(value={'status': 'completed', 'model': 'fixture-model', 'usage': {'total_tokens': 3},
            'output': [{'type': 'reasoning', 'summary': []}, {'type': 'message', 'content': [
                {'type': 'output_text', 'text': 'first'}, {'type': 'output_text', 'text': ' second'}]}]})
        self.assertEqual(result['reply'], 'first second')
        self.assertEqual(result['usage'], {'total_tokens': 3})

    def test_http_errors_and_redirects_do_not_read_response_bodies(self):
        for status in (302, 401, 429, 500):
            with self.subTest(status=status):
                result, response = self.call(status=status, raw=b'untrusted error content')
                self.assertEqual(result, {'status': 'http_error', 'http_status': status, 'reply': ''})
                self.assertEqual(response.reads, 0)

    def test_disconnect_is_a_single_incomplete_attempt(self):
        result, _ = self.call(error=http.client.RemoteDisconnected())
        self.assertEqual(result['status'], 'transport_or_decode_error')

    def test_malformed_json_is_recorded_as_decode_failure(self):
        result, _ = self.call(raw=b'not-json')
        self.assertEqual(result['status'], 'transport_or_decode_error')

    def test_empty_completion_is_not_success(self):
        result, _ = self.call(value={'status': 'completed', 'output': []})
        self.assertEqual(result['status'], 'empty_response')

    def test_incomplete_keeps_partial_text(self):
        result, _ = self.call(value={'status': 'incomplete', 'output': [{'type': 'message', 'content': [{'type': 'output_text', 'text': 'partial'}]}]})
        self.assertEqual(result['status'], 'incomplete')
        self.assertEqual(result['reply'], 'partial')

    def test_oversized_response_is_not_decoded(self):
        result, _ = self.call(raw=b'x' * 2_000_001)
        self.assertEqual(result['status'], 'response_too_large')


if __name__ == '__main__':
    unittest.main()
