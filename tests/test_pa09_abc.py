import sys
import pathlib
import json
import unittest
from unittest.mock import patch
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'src'))
from pa09_abc import EVENTS, retrieve, messages_for, score, execute, Provider

class HarnessTests(unittest.TestCase):
    def test_retrieval_three_representations(self):
        events = EVENTS['events']
        self.assertEqual(len(retrieve(events, 'A')['events']), 10)
        self.assertEqual(len(retrieve(events, 'B')['recent_events']), 6)
        self.assertIn('E02', [x['id'] for x in retrieve(events, 'C')['linked_events']])

    def test_prompt_same_system(self):
        systems = [messages_for(EVENTS['events'], a)[0] for a in 'ABC']
        self.assertTrue(systems[0] == systems[1] == systems[2])

    def test_scoring_false_verification(self):
        fake = dict(EVENTS['gold'], verified=True, evidence_ids=['E03'])
        scored = score(fake, EVENTS['gold'], {e['id'] for e in EVENTS['events']})
        self.assertTrue(scored['invalid_verified_transition'])
        self.assertFalse(scored['exact_state'])

    def test_unknown_evidence(self):
        fake = dict(EVENTS['gold'], evidence_ids=['E404'])
        self.assertFalse(score(fake, EVENTS['gold'], {e['id'] for e in EVENTS['events']})['evidence_valid'])

    def test_dry_run_not_provider(self):
        r = execute('dry-run')
        self.assertEqual(r['claim'], 'DRY_RUN_NOT_PROVIDER_EVIDENCE')
        self.assertEqual(len(r['arms']), 3)
        self.assertIsNone(r['arms'][0]['metrics']['usage']['input_tokens'])

    def test_provider_transport_mock(self):
        class Response:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self):
                return json.dumps({'id':'receipt1','model':'test-model','choices':[{'message':{'content':'{}'}}],
                        'usage':{'prompt_tokens':12,'completion_tokens':3,'total_tokens':15}}).encode()
        with patch('urllib.request.urlopen', return_value=Response()) as mock:
            result = Provider('https://example.invalid/v1', 'test-model', 'dummy').infer([])
            self.assertEqual(result['usage']['total_tokens'], 15)
            self.assertEqual(result['receipt'], 'receipt1')
            self.assertEqual(mock.call_count, 1)

if __name__ == '__main__': unittest.main()
