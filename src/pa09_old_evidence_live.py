"""Old-evidence test: one question, same model, A/B/C retrieval policies."""
import json
import os
from pathlib import Path
from pa09_abc import EVENTS, retrieve, Provider, parse_json

ROOT = Path(__file__).resolve().parents[1]
events = EVENTS['events'] + [
    {'id': 'N%02d' % i, 'type': 'NOISE', 'data': {'message': 'Unrelated note %s' % i}}
    for i in range(1, 13)
]
system = ('Answer using only supplied event evidence. Give JSON with '
          'last_verified_version (integer or null), readback_id (string or null). '
          'If no independent READBACK evidence is available, use null. '
          'Do not infer an earlier verified version from unverified claims.')
gold = {'last_verified_version': 2, 'readback_id': 'E07'}
run = {'mode': 'LIVE_OLD_EVIDENCE' if '--live' in __import__('sys').argv else 'OFFLINE_PREVIEW',
       'gold': gold, 'arms': []}
live = run['mode'] == 'LIVE_OLD_EVIDENCE'
if live:
    provider = Provider(os.environ.get('NEBIUS_BASE_URL', 'https://api.tokenfactory.nebius.com/v1'),
                        os.environ.get('NEBIUS_MODEL', 'nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B'),
                        os.environ['NEBIUS_API_KEY'])
for arm in 'ABC':
    payload = retrieve(events, arm)
    ids = {e['id'] for k in ('events', 'recent_events', 'linked_events')
           for e in payload.get(k, [])}
    row = {'arm': arm, 'has_E07': 'E07' in ids, 'events_supplied': len(ids)}
    if live:
        print('START ' + arm, flush=True)
        ans = provider.infer([{'role':'system','content':system},
            {'role':'user','content':'What was the last independently VERIFIED version? Give the supporting readback event ID.\n'
                                  +json.dumps(payload,separators=(',', ':'))}])
        try:
            row['answer'] = parse_json(ans['content'])
        except ValueError:
            row['answer'] = None
        row['raw_answer'] = ans['content']
        row['usage'] = ans['usage']
        row['latency_ms'] = ans['latency_ms']
        row['correct'] = row['answer'] == (gold if row['has_E07'] else
                                           {'last_verified_version': None, 'readback_id': None})
        print('DONE '+arm+' correct='+str(row['correct']),flush=True)
    run['arms'].append(row)
    (ROOT/'results'/'PA09_OLD_EVIDENCE_LIVE.json' if live else
     ROOT/'results'/'PA09_OLD_EVIDENCE_PREVIEW.json').write_text(
         json.dumps(run,indent=2),encoding='utf-8')
print(json.dumps({'mode':run['mode'], 'arms': [
    {k:v for k,v in row.items() if k not in ('raw_answer',)}
    for row in run['arms']]},indent=2))
