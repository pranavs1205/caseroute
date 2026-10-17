"""Minimal AnyAPI model discovery and chat smoke test. Credentials stay hidden.

python anyapi_smoke.py --list-models
python anyapi_smoke.py MODEL_ID
"""
import argparse
import http.client
import json
import os
from pathlib import Path

HOST = 'api.anyapi.ai'
ENV_PATH = Path(__file__).resolve().parent / '.env'


def load_setting(names, env_path=None):
    """Read only requested settings, with no execution or interpolation."""
    for name in names:
        value = os.environ.get(name, '').strip()
        if value:
            return value
    path = Path(env_path) if env_path else ENV_PATH
    if not path.exists():
        return ''
    for raw in path.read_text(encoding='utf-8-sig').splitlines():
        name, separator, value = raw.strip().removeprefix('export ').partition('=')
        if not separator or name.strip() not in names:
            continue
        value = value.strip()
        if value.startswith('#'):
            continue
        if value.startswith(('"', "'")):
            value = value[1:].split(value[0], 1)[0].strip()
        else:
            value = value.split(' #', 1)[0].strip()
        if value:
            return value
    return ''


def load_key(env_path=None):
    return load_setting(('ANYAPI_API_KEY', 'ANY_API_KEY'), env_path)


def request_json(method, path, key, body=None):
    """Fixed HTTPS host, no redirects, bounded response, no credential logging."""
    connection = http.client.HTTPSConnection(HOST, timeout=55)
    encoded = None if body is None else json.dumps(body, separators=(',', ':')).encode()
    headers = {'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'}
    try:
        connection.request(method, path, body=encoded, headers=headers)
        response = connection.getresponse()
        payload = response.read(2_000_001)
        if len(payload) > 2_000_000:
            raise ValueError('AnyAPI response exceeded the size limit')
        try:
            data = json.loads(payload)
        except (UnicodeDecodeError, json.JSONDecodeError):
            data = {'error': {'code': 'non_json_response'}}
        return response.status, {k.lower(): v for k, v in response.getheaders()}, data
    finally:
        connection.close()


def list_models(key):
    status, _, data = request_json('GET', '/v1/models', key)
    if status != 200:
        # Provider messages may echo input; do not include them in errors/logs.
        raise RuntimeError(f'AnyAPI model listing failed (HTTP {status}). Check credentials and account access.')
    return sorted({item['id'] for item in data.get('data', []) if isinstance(item, dict) and isinstance(item.get('id'), str)})


def chat(key, model):
    return request_json('POST', '/v1/chat/completions', key, {
        'model': model, 'messages': [{'role': 'user', 'content': 'Reply with exactly: AnyAPI smoke test passed'}]})


def main():
    parser = argparse.ArgumentParser(description='Test AnyAPI without exposing credentials.')
    parser.add_argument('model', nargs='?')
    parser.add_argument('--list-models', action='store_true')
    args = parser.parse_args()
    key = load_key()
    if not key:
        raise SystemExit('ANYAPI_API_KEY / ANY_API_KEY was not found in the environment or project .env.')
    print('AnyAPI credential loaded (value hidden).')
    if args.list_models:
        for model in list_models(key):
            print(model)
        return
    if not args.model:
        parser.error('provide MODEL_ID or --list-models')
    status, headers, data = chat(key, args.model)
    if status != 200:
        raise SystemExit(f'AnyAPI smoke test failed (HTTP {status}).')
    choices = data.get('choices') or []
    text = (choices[0].get('message') or {}).get('content') if choices else ''
    usage = data.get('usage') or {}
    print('Model:', data.get('model', args.model))
    print('Response:', text)
    print('Usage: input=%s output=%s total=%s' % (usage.get('prompt_tokens'), usage.get('completion_tokens'), usage.get('total_tokens')))
    print('Request ID present:', bool(headers.get('x-request-id')))
    if not text or text.strip() != 'AnyAPI smoke test passed':
        raise SystemExit('A completion was returned, but the exact smoke-test response was not matched.')


if __name__ == '__main__':
    main()
