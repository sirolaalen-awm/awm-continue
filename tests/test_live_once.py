import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'src'))
from live_once import run

class SingleCallTests(unittest.TestCase):
    def test_consumed_approval_blocks_before_network_or_credential_access(self):
        with tempfile.TemporaryDirectory(dir=pathlib.Path(__file__).resolve().parents[1]) as d:
            (pathlib.Path(d)/'NEMOTRON_SINGLE_CALL.claim').write_text('consumed')
            with patch('urllib.request.build_opener') as network:
                with self.assertRaises(ValueError): run({},d)
                network.assert_not_called()
