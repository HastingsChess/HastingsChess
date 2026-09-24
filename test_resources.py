"""Bundle layout and launch paths; tests run against source and native builds."""
import tempfile,unittest,hashlib
from pathlib import Path
from unittest.mock import patch
import engine_uci
import app

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
 def test_bundled_rules_relative_to_application(self):
  rules=app.ROOT/'IN_GAME_RULES.md'
  self.assertIn('I am not a coder. I just had too much time on my hands and it was Wednesday.',rules.read_text(encoding='utf-8'))
  self.assertIn('On each bonus action, a pawn may advance only one square. However, the same pawn may use both bonus actions',rules.read_text(encoding='utf-8'))
 def test_approved_player_documentation(self):
  guide=Path(__file__).parent/'Honestly, you should probably read this at some point.txt'
  raw=guide.read_bytes()
  self.assertEqual(hashlib.sha256(raw).hexdigest(),'1812cc732fa27bed7dbee87ed11e49cbd9b1d7ca75613f667ab393e9a2cb91e1')
  text=raw.decode('utf-8')
  self.assertIn('20\t1%',text);self.assertIn('30\t100%',text)
  self.assertIn('I just had too much time on my hands and it was Wednesday.',text)

if __name__=='__main__':unittest.main()
