import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from awm_reference import Trace
from pulse_runtime import LocalCouplings, Pulse, inherited_decision, demo_pulse

class PulseTests(unittest.TestCase):
    def setUp(self):
        self.c = LocalCouplings([('A','B'),('B','C')])
    def trace(self, f, cond, status):
        return Trace(f, frozenset(cond), status, '', 'G1', 'evidence1')
    def test_one_hop_only(self):
        r = inherited_decision([self.trace('C',{'x'},'LAST_GOOD')],Pulse('new',frozenset({'A'}),frozenset({'x'})),self.c)
        self.assertEqual(r.function,'NOVI_POKUSAJ')
    def test_contextual_compost_blocks_same_conditions(self):
        t=[self.trace('B',{'soft'},'LAST_GOOD'),self.trace('B',{'soft'},'KOMPOST')]
        r=inherited_decision(t,Pulse('new',frozenset({'A'}),frozenset({'soft'})),self.c)
        self.assertIn('B',r.blocked_functions)
        self.assertEqual(r.function,'NOVI_POKUSAJ')
    def test_failure_not_global_ban(self):
        t=[self.trace('B',{'soft'},'KOMPOST'),self.trace('B',{'hard'},'LAST_GOOD')]
        r=inherited_decision(t,Pulse('new',frozenset({'A'}),frozenset({'hard'})),self.c)
        self.assertEqual(r.function,'B')
        self.assertNotIn('B',r.blocked_functions)
    def test_potential_remains_candidate(self):
        t=[self.trace('B',{'hard'},'OTVORENI_POTENCIJAL')]
        r=inherited_decision(t,Pulse('new',frozenset({'A'}),frozenset({'hard'})),self.c)
        self.assertEqual(r.function,'B')
        self.assertIn('OTVORENI_POTENCIJAL',r.reason)
    def test_demo_relevant_function(self):
        r=demo_pulse()
        self.assertEqual(r.function,'F_NISKA_SILA')
    def test_no_shared_condition_not_claimed(self):
        t=[self.trace('B',{'soft'},'LAST_GOOD')]
        r=inherited_decision(t,Pulse('new',frozenset({'A'}),frozenset({'hard'})),self.c)
        self.assertEqual(r.function,'NOVI_POKUSAJ')

if __name__ == '__main__': unittest.main()
