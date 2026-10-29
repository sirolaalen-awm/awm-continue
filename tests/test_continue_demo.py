import pathlib
import sys
import tempfile
import unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'src'))
from continue_demo import Memory

class ContinuityTests(unittest.TestCase):
    def test_restart_preserves_checkpoint_and_later_changes(self):
        with tempfile.TemporaryDirectory(dir=pathlib.Path(__file__).resolve().parents[1]) as d:
            path=pathlib.Path(d)/'memory.sqlite'
            m=Memory(path); m.add('checkpoint','Draft complete; review budget next.'); m.db.close()
            m=Memory(path); m.add('update','Budget reduced to 500.'); m.db.close()
            m=Memory(path); r=m.resume(); m.db.close()
            self.assertEqual(r['checkpoint'][2],'Draft complete; review budget next.')
            self.assertEqual(r['updates'][0][2],'Budget reduced to 500.')
    def test_new_checkpoint_does_not_repeat_old_updates(self):
        m=Memory(':memory:'); m.add('update','Old'); m.add('checkpoint','New'); self.assertEqual(m.resume()['updates'],[])
    def test_empty_and_unknown_events_rejected(self):
        m=Memory(':memory:')
        for kind,text in [('checkpoint',''),('verified','claim')]:
            with self.assertRaises(ValueError): m.add(kind,text)

