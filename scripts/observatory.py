#!/usr/bin/env python3
"""Run from a source checkout; Python standard library only."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'runtime'))
from field_observatory.prompts import LANGUAGES, MODES, catalog, compile_prompt
from field_observatory.provider import DEFAULT_MODEL, Session, request_body
from field_observatory.server import make_server
from field_observatory.signals import verify_samples


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    signals = sub.add_parser('verify-signals')
    signals.add_argument('--portable', action='store_true', help='Check recorded hashes and every decision with a fixed absolute numeric tolerance')
    export = sub.add_parser('prompt')
    run = sub.add_parser('run')
    for p in (export, run):
        p.add_argument('--preset', default='quiet-dialogue', choices=list(catalog()[1]))
        p.add_argument('--mode', default='structured', choices=MODES)
        p.add_argument('--language', default='en', choices=LANGUAGES, help='Language of the system instructions, independent of the input language')
        p.add_argument('--fields', nargs='*', help='Ordered Field IDs; overrides the preset selection')
    run.add_argument('--input-file', required=True, type=Path)
    run.add_argument('--execute', action='store_true', help='Send exactly one live API request; default prints a preview')
    server = sub.add_parser('serve')
    server.add_argument('--port', type=int, default=8768)
    server.add_argument('--enable-api', action='store_true')
    server.add_argument('--max-requests', type=int, default=3)
    for p in (run, server):
        p.add_argument('--model', default=DEFAULT_MODEL)
        p.add_argument('--max-output-tokens', type=int, default=600)
        p.add_argument('--records', type=Path, default=ROOT / '.runs')
    args = parser.parse_args()
    if args.command == 'prompt':
        value = compile_prompt(args.preset, args.mode, language=args.language, field_ids=args.fields)
    elif args.command == 'verify-signals':
        value = verify_samples(portable=args.portable)
    elif args.command == 'run':
        text = args.input_file.read_text()
        if args.execute:
            value = Session(enabled=True, model=args.model, limit=1, output_tokens=args.max_output_tokens,
                            records=args.records).run(text, args.preset, args.mode, language=args.language, field_ids=args.fields)
        else:
            body, prompt = request_body(text, args.preset, args.mode, args.model, args.max_output_tokens, language=args.language, field_ids=args.fields)
            value = {'status': 'preview_only_no_request_sent', 'request': body, 'prompt': prompt}
    else:
        session = Session(enabled=args.enable_api, model=args.model, limit=args.max_requests,
                          output_tokens=args.max_output_tokens, records=args.records)
        server = make_server(session, args.port)
        print(f'Field Observatory: http://127.0.0.1:{server.server_port} · live API {"enabled" if args.enable_api else "disabled"}', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()
        return 0
    print(json.dumps(value, ensure_ascii=False, indent=2))
    return 0 if value.get('status', 'completed') in ('completed', 'preview_only_no_request_sent') else 1


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError):
        print('Could not complete the command. Check input, configuration and local output permissions.', file=sys.stderr)
        raise SystemExit(1)
