import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from inherited_pulse import Experience, ProcessState, inherit_pulse, example_generation1

class InheritedPulseTests(unittest.TestCase):
    def setUp(self):
        self.gen1 = example_generation1()
        self.ctx = frozenset({'awc_process'})

    def test_gen2_pulse_continues_when_next_exists(self):
        r = inherit_pulse('.', ProcessState('OPEN', 'izvedi_korak_2', self.ctx), self.gen1)
        self.assertEqual((r.action, r.product), ('CONTINUE', 'izvedi_korak_2'))
        self.assertTrue(r.evidence)

    def test_gen2_pulse_stops_when_complete(self):
        r = inherit_pulse('.', ProcessState('COMPLETE', '', self.ctx), self.gen1)
        self.assertEqual((r.action, r.product), ('STOP', 'POTREBAN_NOVI_ULAZ'))

    def test_unverified_memory_does_not_activate(self):
        rumor = [Experience('.', 'PULSE_CLOCK', self.ctx, 'OTVORENI_POTENCIJAL', '')]
        self.assertEqual(inherit_pulse('.', ProcessState('OPEN', 'k2', self.ctx), rumor).action, 'UNKNOWN')

    def test_changed_conditions_do_not_inherit_wrong_rule(self):
        self.assertEqual(inherit_pulse('.', ProcessState('OPEN', 'k2', frozenset({'novi_proces'})), self.gen1).action, 'UNKNOWN')

    def test_no_next_without_complete_is_unknown(self):
        self.assertEqual(inherit_pulse('.', ProcessState('OPEN', '', self.ctx), self.gen1).action, 'UNKNOWN')

    def test_not_an_unconditional_continue_command(self):
        self.assertEqual(inherit_pulse('nastavi', ProcessState('OPEN', 'k2', self.ctx), self.gen1).action, 'UNKNOWN')

if __name__ == '__main__': unittest.main()
