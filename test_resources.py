"""Bundle layout and launch paths; tests run against source and native builds."""
import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import engine_uci

class ResourceTests(unittest.TestCase):
 def test_platform_filenames(self):
  self.assertEqual(engine_uci.engine_filename('win32','AMD64'),'fairy-stockfish.exe')
  self.assertEqual(engine_uci.engine_filename('darwin','arm64'),'fairy-stockfish-macos-arm64')
  self.assertEqual(engine_uci.engine_filename('darwin','x86_64'),'fairy-stockfish-macos-x86_64')
  self.assertEqual(engine_uci.engine_filename('linux','x86_64'),'fairy-stockfish-linux')
 def test_resources_relative_to_bundle_even_when_cwd_differs(self):
  with tempfile.TemporaryDirectory(prefix='Hastings Chess portable ') as d:
   base=Path(d)/'Hastings Chess'/'_internal';(base/'engine').mkdir(parents=True)
   (base/'engine'/'hastings.ini').write_text('[hastings:chess]')
   with patch.object(engine_uci,'BASE',base),patch.object(engine_uci,'engine_filename',return_value='fairy-stockfish.exe'):
    self.assertEqual(engine_uci.default_engine(),base/'engine'/'fairy-stockfish.exe')
    self.assertTrue((engine_uci.BASE/'engine'/'hastings.ini').is_file())

if __name__=='__main__':unittest.main()
