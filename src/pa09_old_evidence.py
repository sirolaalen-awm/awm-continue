import json
from pathlib import Path
from pa09_abc import EVENTS, retrieve
root = Path(__file__).resolve().parents[1]
events = EVENTS['events'] + [{'id': 'N%02d' % i, 'type': 'NOISE', 'data': {'message': 'Unrelated note %s' % i}} for i in range(1,13)]
seen = {}
for arm in 'ABC':
    r = retrieve(events, arm)
    ids = [e['id'] for k in ('events','recent_events','linked_events') for e in r.get(k, [])]
    seen[arm] = {'has_readback_E07': 'E07' in ids, 'events_supplied': len(ids)}
result = {'mode': 'OFFLINE_EVIDENCE_COVERAGE_NOT_INFERENCE', 'arms': seen}
assert [seen[a]['has_readback_E07'] for a in 'ABC'] == [True,False,True]
out = root/'results'/'PA09_OLD_EVIDENCE_OFFLINE.json'
out.write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
