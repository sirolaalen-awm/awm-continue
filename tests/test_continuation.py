import json
import pathlib
import sys
import unittest
from unittest.mock import Mock
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'src'))
from continuation import prepare, validate, continue_with_provider

class ContinuationTests(unittest.TestCase):
    def setUp(self):
        self.state={'checkpoint':(1,'checkpoint','Brief drafted'),
                    'updates':[(2,'update','Budget now 500 EUR')]}
        self.answer={'summary':'Brief drafted; budget changed to 500 EUR.',
                     'next_step':'Review budget before proceeding.',
                     'evidence_ids':['E1','E2'],'status':'proposal'}
    def test_no_provider_call_without_cost_approval(self):
        transport=Mock()
        with self.assertRaises(PermissionError): continue_with_provider(self.state,transport)
        transport.assert_not_called()
    def test_current_user_state_reaches_transport_and_citations_return(self):
        transport=Mock(return_value={'content':json.dumps(self.answer),'receipt':'MOCK_ONLY'})
        result=continue_with_provider(self.state,transport,approved=True)
        self.assertIn('500 EUR',transport.call_args.args[0][1]['content'])
        self.assertEqual(transport.call_args.kwargs['max_tokens'],350)
        self.assertEqual(result['answer']['citation_validation'],'PASS')
        self.assertFalse(result['verified'])
    def test_missing_update_or_fabricated_citation_rejected(self):
        for ids in [['E1'],['E1','E999'],[]]:
            self.answer['evidence_ids']=ids
            with self.assertRaises(ValueError): validate(json.dumps(self.answer),prepare(self.state))
    def test_false_status_rejected(self):
        self.answer['status']='verified'
        with self.assertRaises(ValueError): validate(json.dumps(self.answer),prepare(self.state))
    def test_no_checkpoint_means_no_inference(self):
        with self.assertRaises(ValueError): prepare({'checkpoint':None,'updates':[]})
