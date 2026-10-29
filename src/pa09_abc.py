"""PA-09 A/B/C execution harness. Standard library only. Network is opt-in.

Dry-run is a wiring test, NOT an inference nor evidence of AWM advantage.
"""
import argparse
import datetime as dt
import json
import os
import pathlib
import re
import time
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass

ROOT = pathlib.Path(__file__).resolve().parents[1]
EVENTS = json.loads((ROOT / 'fixtures' / 'process_events.json').read_text(encoding='utf-8'))
ARMS = ('A', 'B', 'C')
FIELDS = ('version', 'owner', 'status', 'value', 'authorized', 'executed', 'verified')


def retrieve(events, arm):
    """Different presentation/memory policies, same underlying events and final question."""
    if arm == 'A':
        return {'mode': 'linear', 'events': events}
    if arm == 'B':
        # Standard retrieval: only recent tail in recency order, same token-budget direction as C.
        return {'mode': 'recency_memory', 'recent_events': events[-6:]}
    if arm == 'C':
        # Functional retrieval: status-bearing events, old evidence & corrections, no answer injection.
        relevant = [e for e in events if e['type'] in ('STATE', 'AUTH', 'EXEC', 'READBACK', 'CORRECTION', 'CONFLICT')]
        return {'mode': 'functional_memory',
                'local_pulse': 'state_review',
                'linked_events': [{'id': e['id'], 'type': e['type'], 'data': e['data']} for e in relevant],
                'transition_rule': 'UNDERSTOOD != AUTHORIZED != EXECUTED != VERIFIED; absence of independent readback means verified=false',
                'classification': {'last_good': 'independent readback only',
                                   'compost': 'contradictions/failed attempts stay contextual',
                                   'open_potential': 'not-yet-executed actions are proposals'}}
    raise ValueError(arm)


SYSTEM = ('You are a process-state auditor. Use ONLY the supplied event evidence. '
          'Return ONLY JSON with exactly these keys: version (integer), owner (string), '
          'status (string), value (integer), authorized (boolean), executed (boolean), '
          'verified (boolean), evidence_ids (array of event ids), explanation (short string). '
          'If a transition has no independent evidence, do not promote its status.')


def messages_for(events, arm):
    payload = retrieve(events, arm)
    return [{'role': 'system', 'content': SYSTEM},
            {'role': 'user', 'content': 'Reconstruct current process state from this representation.\n'
                    + json.dumps(payload, ensure_ascii=False, separators=(',', ':'))}]


def parse_json(text):
    text = text.strip()
    if text.startswith('```'):
        text = re.sub(r'^```(?:json)?\s*|\s*```$', '', text, flags=re.I)
    obj = json.loads(text)
    if not isinstance(obj, dict):
        raise ValueError('response is not JSON object')
    return obj


def score(obj, gold, valid_ids):
    errors = {}
    for field in FIELDS:
        if field not in obj or type(obj[field]) is not type(gold[field]) or obj[field] != gold[field]:
            errors[field] = {'expected': gold[field], 'actual': obj.get(field)}
    ids = obj.get('evidence_ids')
    invalid_evidence = not isinstance(ids, list) or any(i not in valid_ids for i in ids)
    if invalid_evidence:
        errors['evidence_ids'] = 'missing or fabricated event ID'
    # independent readback is essential for VERIFIED; a model's claim does not validate it
    invalid_transition = bool(obj.get('verified') is True and not any(
        e['type'] == 'READBACK' and e['id'] in (ids if isinstance(ids, list) else []) and e['data'].get('version') == obj.get('version')
        for e in EVENTS['events']))
    return {'state_accuracy': (len(FIELDS) - sum(k in errors for k in FIELDS)) / len(FIELDS),
            'exact_state': not any(k in errors for k in FIELDS),
            'evidence_valid': not invalid_evidence,
            'invalid_verified_transition': invalid_transition,
            'errors': errors}


@dataclass
class Provider:
    url: str
    model: str
    api_key: str
    timeout: int = 60

    def infer(self, messages):
        payload = json.dumps({'model': self.model, 'messages': messages, 'temperature': 0,
                              'stream': False}).encode('utf-8')
        request = urllib.request.Request(self.url.rstrip('/') + '/chat/completions', data=payload,
            headers={'Authorization': 'Bearer ' + self.api_key,
                     'Content-Type': 'application/json'}, method='POST')
        start = time.perf_counter()
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            raw = response.read()
            status = response.status
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        body = json.loads(raw)
        choices = body.get('choices') or []
        content = choices[0]['message'].get('content') if choices else None
        if not isinstance(content, str):
            raise ValueError('provider returned no text content')
        usage = body.get('usage') or {}
        return {'content': content, 'latency_ms': latency_ms, 'http_status': status,
                'usage': {'input_tokens': usage.get('prompt_tokens'),
                          'output_tokens': usage.get('completion_tokens'),
                          'total_tokens': usage.get('total_tokens')},
                'receipt': body.get('id'), 'model_readback': body.get('model')}


def execute(mode, model='', url='', key='', output=None):
    events = EVENTS['events']
    gold = EVENTS['gold']
    valid_ids = {e['id'] for e in events}
    artifact = {'run_id': str(uuid.uuid4()), 'timestamp_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
                'mode': mode, 'provider': 'OpenAI-compatible API' if mode == 'live' else 'LOCAL_MOCK',
                'model_requested': model if mode == 'live' else None,
                'task_id': EVENTS['task_id'], 'arms': [],
                'claim': 'LIVE_INFERENCE' if mode == 'live' else 'DRY_RUN_NOT_PROVIDER_EVIDENCE'}
    provider = Provider(url, model, key) if mode == 'live' else None
    for arm in ARMS:
        print('PA09 START ' + arm, flush=True)
        messages = messages_for(events, arm)
        if mode == 'live':
            result = provider.infer(messages)
            content = result['content']
        else:
            # Explicit canned response, useful solely for exercising plumbing/scoring.
            content = json.dumps(dict(gold, evidence_ids=['E02', 'E04', 'E07', 'E10'],
                                      explanation='CANNED local response; not model inference'))
            result = {'latency_ms': None, 'http_status': None,
                      'usage': {'input_tokens': None, 'output_tokens': None, 'total_tokens': None},
                      'receipt': None, 'model_readback': None}
        try:
            obj = parse_json(content)
            evaluation = score(obj, gold, valid_ids)
        except (ValueError, json.JSONDecodeError) as exc:
            obj = None
            evaluation = {'state_accuracy': 0, 'exact_state': False, 'evidence_valid': False,
                          'invalid_verified_transition': False, 'errors': {'parse': str(exc)}}
        artifact['arms'].append({'arm': arm, 'input_representation': retrieve(events, arm),
                                 'messages': messages, 'result': obj, 'evaluation': evaluation,
                                 'metrics': result})
        print('PA09 DONE ' + arm + ' score=' + str(evaluation['state_accuracy']), flush=True)
        if output:
            partial = pathlib.Path(output)
            partial.parent.mkdir(parents=True, exist_ok=True)
            partial.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding='utf-8')
    if output:
        path = pathlib.Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding='utf-8')
    return artifact


def main():
    p = argparse.ArgumentParser(description='PA-09 A/B/C; offline by default; live requires explicit --live')
    p.add_argument('--dry-run', action='store_true', help='no network, canned answers')
    p.add_argument('--live', action='store_true', help='makes three billable/remote model requests')
    p.add_argument('--output', default='results/pa09_run.json')
    args = p.parse_args()
    if args.live == args.dry_run:
        p.error('choose exactly one of --dry-run or --live')
    model = os.environ.get('NEBIUS_MODEL', '')
    url = os.environ.get('NEBIUS_BASE_URL', '')
    key = os.environ.get('NEBIUS_API_KEY', '')
    if args.live and (not model or not url or not key):
        p.error('live requires NEBIUS_MODEL, NEBIUS_BASE_URL and NEBIUS_API_KEY environment variables')
    try:
        r = execute('live' if args.live else 'dry-run', model, url, key, args.output)
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        p.exit(2, 'ACCESS_OR_PROVIDER_ERROR: ' + str(exc) + '\n')
    print(json.dumps({'mode': r['mode'], 'result_file': args.output,
                      'arms': [{ 'arm': a['arm'], 'score': a['evaluation']['state_accuracy'],
                                 'input_tokens': a['metrics']['usage']['input_tokens'],
                                 'latency_ms': a['metrics']['latency_ms']} for a in r['arms']]},
                     ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
