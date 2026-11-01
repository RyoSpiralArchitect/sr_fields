"""One bounded OpenAI request. No implicit retry, redirects, tools or history."""
import http.client
import json
import os
import re
import ssl
import threading
import time
import uuid
from pathlib import Path
from .prompts import ROOT, compile_prompt, digest, encoded

DEFAULT_MODEL = 'gpt-6-sol'


def request_body(text, preset, mode, model=DEFAULT_MODEL, max_output_tokens=600, *, language='en', field_ids=None):
    if not isinstance(text, str) or not text.strip() or len(text) > 4000:
        raise ValueError('Input must contain 1–4000 characters')
    if not isinstance(model, str) or not re.fullmatch(r'[A-Za-z0-9._-]{1,100}', model):
        raise ValueError('Invalid model name')
    if type(max_output_tokens) is not int or not 16 <= max_output_tokens <= 1200:
        raise ValueError('Output cap must be 16–1200 tokens')
    prompt = compile_prompt(preset, mode, language=language, field_ids=field_ids)
    body = {'model': model, 'instructions': prompt['instructions'], 'input': text,
            'reasoning': {'effort': 'none'}, 'max_output_tokens': max_output_tokens, 'store': False}
    return body, {k: v for k, v in prompt.items() if k != 'instructions'}


def transport(body, key):
    """Fixed first-party endpoint; error bodies are not returned or persisted."""
    connection = http.client.HTTPSConnection('api.openai.com', timeout=45, context=ssl.create_default_context())
    try:
        connection.request('POST', '/v1/responses', body=encoded(body),
                           headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
        response = connection.getresponse()
        if response.status != 200:
            return {'status': 'http_error', 'http_status': response.status, 'reply': ''}
        raw = response.read(2_000_001)
        if len(raw) > 2_000_000:
            return {'status': 'response_too_large', 'reply': ''}
        value = json.loads(raw)
        reply = ''.join(part.get('text', '') for item in value.get('output', []) if item.get('type') == 'message'
                        for part in item.get('content', []) if part.get('type') == 'output_text')
        status = value.get('status')
        if status == 'completed' and not reply.strip():
            status = 'empty_response'
        return {'status': status or 'unknown_response', 'reply': reply,
                'model': value.get('model'), 'usage': value.get('usage')}
    except (OSError, ValueError, TypeError, KeyError, http.client.HTTPException):
        return {'status': 'transport_or_decode_error', 'reply': ''}
    finally:
        connection.close()


def private_write(path, value):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'wb') as handle:
        handle.write(encoded(value))


class Session:
    """Per-process budget. A dispatched failure closes the session."""
    def __init__(self, *, enabled=False, model=DEFAULT_MODEL, limit=3, output_tokens=600, records=None, send=transport):
        if type(limit) is not int or not 1 <= limit <= 18:
            raise ValueError('Session limit must be 1–18 requests')
        request_body('validate', 'quiet-dialogue', 'baseline', model, output_tokens)
        self.enabled, self.model, self.limit = enabled, model, limit
        self.output_tokens, self.records, self.send = output_tokens, Path(records).resolve() if records else None, send
        if self.records and self.records.is_relative_to(ROOT):
            if not any(self.records.is_relative_to(ROOT / name) for name in ('.runs', '.private')):
                raise ValueError('Run records inside the repository must use .runs or .private')
        self.attempted, self.stopped = 0, False
        self.lock = threading.Lock()

    def info(self):
        return {'enabled': self.enabled, 'model': self.model, 'attempted': self.attempted,
                'limit': self.limit, 'stopped': self.stopped, 'max_output_tokens': self.output_tokens}

    def run(self, text, preset, mode, *, language='en', field_ids=None):
        with self.lock:
            if not self.enabled:
                raise ValueError('Live API is disabled for this server')
            if self.stopped or self.attempted >= self.limit:
                raise ValueError('Session stopped or request budget exhausted')
            key = os.environ.get('OPENAI_API_KEY')
            if not key:
                raise ValueError('OPENAI_API_KEY is unavailable in the server environment')
            body, prompt = request_body(text, preset, mode, self.model, self.output_tokens, language=language, field_ids=field_ids)
            if key in encoded(body).decode():
                raise ValueError('Credential content must not be sent as input')
            run_id = uuid.uuid4().hex
            directory = None
            if self.records:
                self.records.mkdir(mode=0o700, parents=True, exist_ok=True)
                directory = self.records / run_id
                directory.mkdir(mode=0o700)
                private_write(directory / 'request.json', body)
                private_write(directory / 'dispatch.json', {'index': self.attempted + 1, 'prompt': prompt,
                              'request_sha256': digest(encoded(body)), 'retries': 0})
            self.attempted += 1
            started = time.monotonic()
            # Conservatively close on unexpected errors too; never redispatch.
            self.stopped = True
            result = self.send(body, key)
            if key in encoded(result).decode():
                result = {'status': 'credential_echo_blocked', 'reply': ''}
            result = {**result, 'run_id': run_id, 'elapsed_seconds': round(time.monotonic() - started, 3), 'prompt': prompt}
            if directory:
                private_write(directory / 'result.json', result)
                private_write(directory / 'receipt.json', {'files': {
                    p.name: digest(p.read_bytes()) for p in sorted(directory.iterdir()) if p.is_file()}})
            self.stopped = result['status'] != 'completed'
            return result
