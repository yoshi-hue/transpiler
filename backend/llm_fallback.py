"""Auditable, optional LLM fallback for unsupported translation constructs.

The LLM is never treated as a source of truth. It receives the smallest unsupported
construct plus compiler context, returns a candidate target fragment, and the caller
records latency/model/prompt version and keeps the candidate separate from validated
translation output.

Supports both:
  * OpenAI Responses API (recommended)
  * OpenAI-compatible chat-completions endpoints

Configuration is environment-based so API keys never enter the browser UI:
  LLM_API_URL=https://api.openai.com/v1/responses
  LLM_MODEL=<model id>
  LLM_API_KEY=<secret>
  LLM_API_MODE=responses   # or chat
  LLM_PROVIDER=OpenAI
"""
import hashlib
import json
import os
import time
import urllib.error
import urllib.request
import uuid

PROMPT_VERSION = "legacy-modernizer-llm-v2"
DEFAULT_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "45"))
MAX_CONTEXT = int(os.getenv("LLM_MAX_CONTEXT", "7000"))
MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "2"))


def _clean(value):
    return (value or '').strip()


def _is_placeholder_value(value):
    cleaned = _clean(value)
    if not cleaned:
        return False
    lowered = cleaned.lower()
    placeholder_tokens = (
        'your_api_key_here',
        'your_provider_api_key_here',
        'replace_with_your_key',
        'replace_with_your_api_key',
        'example',
        'changeme',
        'dummy',
        'test-key',
        'test_key',
        '<your-key>',
        '<your_api_key>',
    )
    return lowered in placeholder_tokens or lowered.startswith('your_') or lowered.startswith('replace_with_') or lowered.startswith('<your')


class FallbackLog:
    def __init__(self):
        self.entries = []

    def record(self, construct, reason='No deterministic rule available', action='LLM fallback requested', result=None, **metadata):
        entry = {
            'request_id': metadata.pop('request_id', str(uuid.uuid4())[:8]),
            'construct': construct,
            'reason': reason,
            'action': action,
        }
        if result is not None:
            entry['result'] = result
        entry.update({k: v for k, v in metadata.items() if v is not None})
        self.entries.append(entry)
        return entry


def _configured():
    url = _clean(os.getenv('LLM_API_URL'))
    model = _clean(os.getenv('LLM_MODEL'))
    key = _clean(os.getenv('LLM_API_KEY'))
    if _is_placeholder_value(url) or _is_placeholder_value(model):
        return False
    if key and _is_placeholder_value(key):
        return False
    return bool(url and model)


def fallback_status():
    mode = os.getenv('LLM_API_MODE', 'auto').lower()
    key = _clean(os.getenv('LLM_API_KEY'))
    return {
        'configured': _configured(),
        'provider': os.getenv('LLM_PROVIDER', 'OpenAI-compatible endpoint'),
        'model': os.getenv('LLM_MODEL', ''),
        'endpoint_set': bool(_clean(os.getenv('LLM_API_URL'))) and not _is_placeholder_value(os.getenv('LLM_API_URL')),
        'key_set': bool(key) and not _is_placeholder_value(key),
        'api_mode': mode,
        'prompt_version': PROMPT_VERSION,
        'timeout_seconds': DEFAULT_TIMEOUT,
        'max_retries': MAX_RETRIES,
    }


def _headers():
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    key = os.getenv('LLM_API_KEY')
    if key:
        headers['Authorization'] = f'Bearer {key}'
    extra_headers = os.getenv('LLM_EXTRA_HEADERS', '').strip()
    if extra_headers:
        try:
            parsed = json.loads(extra_headers)
            if isinstance(parsed, dict):
                headers.update({str(k): str(v) for k, v in parsed.items()})
        except json.JSONDecodeError:
            pass
    for header_name in ('HTTP_REFERER', 'X_TITLE'):
        value = os.getenv(header_name)
        if value:
            headers[header_name.replace('_', '-').title().replace('-', '-')] = value
    return headers


def _extract_text(body):
    # OpenAI Responses API: output -> message -> content -> output_text
    if isinstance(body, dict):
        if isinstance(body.get('output_text'), str):
            return body['output_text'].strip()
        output = body.get('output')
        if isinstance(output, list):
            chunks = []
            for item in output:
                for content in item.get('content', []) if isinstance(item, dict) else []:
                    if isinstance(content, dict) and isinstance(content.get('text'), str):
                        chunks.append(content['text'])
            if chunks:
                return '\n'.join(chunks).strip()
        # OpenAI-compatible chat-completions
        try:
            content = body['choices'][0]['message']['content']
            if isinstance(content, str):
                return content.strip()
            if isinstance(content, list):
                return ''.join(x.get('text', '') for x in content if isinstance(x, dict)).strip()
        except (KeyError, IndexError, TypeError):
            pass
    raise RuntimeError('LLM response did not contain readable output text.')


def _strip_fences(text):
    text = text.strip()
    if text.startswith('```'):
        parts = text.split('\n', 1)
        text = parts[1] if len(parts) == 2 else ''
        if text.rstrip().endswith('```'):
            text = text.rstrip()[:-3].rstrip()
    return text.strip()


def _mode():
    mode = os.getenv('LLM_API_MODE', 'auto').lower()
    if mode in ('responses', 'chat'):
        return mode
    url = os.getenv('LLM_API_URL', '').lower()
    return 'responses' if url.endswith('/responses') else 'chat'


def _payload(source_language, target_language, construct, context):
    system = (
        'You are a constrained compiler-assistance component. '
        'Translate only the supplied unsupported construct. Preserve names, literals, '
        'control-flow intent and side-effect order. Do not invent APIs or missing logic. '
        'Return ONLY the target-language code fragment; no markdown, explanation, or prose.'
    )
    user = f"""Translation task\nSource language: {source_language}\nTarget language: {target_language}\n\nSurrounding compiler context:\n{context[:MAX_CONTEXT]}\n\nUnsupported construct:\n{construct}\n\nConstraints:\n1. Produce target-language code only.\n2. Keep the fragment small and composable.\n3. If the construct cannot be translated faithfully, return a single comment beginning with UNSUPPORTED rather than inventing behavior.\n"""
    if _mode() == 'responses':
        return {
            'model': os.getenv('LLM_MODEL'),
            'instructions': system,
            'input': user,
            'temperature': 0,
        }
    return {
        'model': os.getenv('LLM_MODEL'),
        'messages': [{'role': 'system', 'content': system}, {'role': 'user', 'content': user}],
        'temperature': 0,
    }


def translate_construct(source_language, target_language, construct, context=''):
    """Request one scoped candidate fragment and return an auditable result dict."""
    if not _configured():
        raise RuntimeError('LLM fallback is not configured. Set LLM_API_URL and LLM_MODEL.')

    request_id = str(uuid.uuid4())
    prompt_material = f'{PROMPT_VERSION}|{source_language}|{target_language}|{construct}|{context[:MAX_CONTEXT]}'
    prompt_hash = hashlib.sha256(prompt_material.encode('utf-8')).hexdigest()[:16]
    payload = _payload(source_language, target_language, construct, context)
    data = json.dumps(payload).encode('utf-8')
    headers = _headers()
    last_error = None
    started = time.perf_counter()

    for attempt in range(MAX_RETRIES + 1):
        try:
            request = urllib.request.Request(os.getenv('LLM_API_URL'), data=data, headers=headers, method='POST')
            with urllib.request.urlopen(request, timeout=DEFAULT_TIMEOUT) as response:
                body = json.loads(response.read().decode('utf-8'))
                status_code = response.status
            text = _strip_fences(_extract_text(body))
            latency_ms = round((time.perf_counter() - started) * 1000, 1)
            if not text:
                raise RuntimeError('LLM returned an empty candidate.')
            return {
                'request_id': request_id,
                'candidate': text,
                'accepted': False,
                'validation_status': 'not_run',
                'provider': os.getenv('LLM_PROVIDER', 'OpenAI-compatible endpoint'),
                'model': os.getenv('LLM_MODEL', ''),
                'api_mode': _mode(),
                'prompt_version': PROMPT_VERSION,
                'prompt_hash': prompt_hash,
                'attempts': attempt + 1,
                'http_status': status_code,
                'latency_ms': latency_ms,
            }
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode('utf-8', errors='replace')
            last_error = f'HTTP {exc.code}: {detail[:300]}'
            if exc.code == 401 or exc.code == 403 or (exc.code == 429 and 'insufficient_quota' in detail):
                break
        except urllib.error.URLError as exc:
            last_error = f'Connection error: {exc.reason}'
        except (TimeoutError, json.JSONDecodeError, RuntimeError) as exc:
            last_error = str(exc)
        if attempt < MAX_RETRIES:
            time.sleep(0.5 * (2 ** attempt))

    latency_ms = round((time.perf_counter() - started) * 1000, 1)
    raise RuntimeError(f'LLM request failed after {MAX_RETRIES + 1} attempt(s): {last_error} [{request_id}, {latency_ms} ms]')


def test_connection():
    """Make a tiny real request to verify endpoint/model credentials.

    This is deliberately separate from translation so a connectivity check cannot
    accidentally become a claimed translation result.
    """
    if not _configured():
        return {'ok': False, 'message': 'LLM is not configured.', 'status': fallback_status()}
    try:
        result = translate_construct('BASIC', 'JavaScript', 'PRINT 2 + 2', '10 PRINT 2 + 2')
    except RuntimeError as exc:
        return {
            'ok': False,
            'message': str(exc),
            'status': fallback_status(),
        }
    candidate = result['candidate']
    return {
        'ok': not candidate.upper().startswith('UNSUPPORTED'),
        'message': 'Real LLM request completed.' if candidate else 'LLM returned no candidate.',
        'candidate_preview': candidate[:200],
        'request_id': result['request_id'],
        'latency_ms': result['latency_ms'],
        'model': result['model'],
        'provider': result['provider'],
        'prompt_version': result['prompt_version'],
    }


def create_fallback_log():
    return FallbackLog()
