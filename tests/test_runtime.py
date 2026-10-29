import sys
import unittest
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from awm_reference import Memory, Verdict, Trace, sentinel, choose_from_experience, run_two_generations

class ProcessTests(unittest.TestCase):
    def test_sentinel_valid_invalid_unknown(self):
        self.assertEqual(sentinel(10,10,"P","dokaz"), Verdict.VALID)
        self.assertEqual(sentinel(11,10,"P","dokaz"), Verdict.INVALID)
        self.assertEqual(sentinel(10,10,"P",None), Verdict.UNKNOWN)

    def test_two_branches_one_commit(self):
        m=Memory()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(lambda x: m.commit(10,x,"dokaz"), ("A","B")))
        self.assertEqual(results.count(Verdict.VALID),1)
        self.assertEqual(results.count(Verdict.INVALID),1)
        self.assertEqual(m.version,11)

    def test_inheritance_open_potential(self):
        m=Memory()
        m.traces.extend([
            Trace("LOSA_SILA", frozenset(["mekan"]), "KOMPOST", "lose", "G1", "rd1"),
            Trace("NOVA_SILA", frozenset(["tvrd"]), "OTVORENI_POTENCIJAL", "otvoreno", "G1", "rd2")])
        self.assertEqual(choose_from_experience(m,{"tvrd", "vruc"})[0],"NOVA_SILA")

    def test_two_generations(self):
        result=run_two_generations()
        self.assertEqual(result["function"], "F_NISKA_SILA")
        self.assertEqual(result["sentinel"], "VALJANO")
        self.assertEqual(result["version"],11)
        self.assertEqual(result["traces"],4)

    def test_unknown_never_promoted(self):
        m=Memory()
        self.assertEqual(m.commit(10,"P",None), Verdict.UNKNOWN)
        self.assertEqual(m.version,10)
        self.assertEqual(m.last_good,"INIT")

if __name__=="__main__": unittest.main()
