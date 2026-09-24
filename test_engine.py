"""These tests invoke the ACTUAL bundled Fairy-Stockfish process."""
import unittest,random,json,shutil,tempfile
from unittest.mock import patch
import engine_uci
from pathlib import Path
import rules as r
from game import Game
from engine_uci import FairyEngine,compatible,fen,uci_move,IncompatiblePosition
from hybrid import Hybrid
from tests import position,at

class RealEngineTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.e=FairyEngine()
 @classmethod
 def tearDownClass(cls):cls.e.close()
 def same_moves(self,s,side):
  self.assertEqual(self.e.legal_moves(s,side),{uci_move(m) for m in r.legal(s,side)})
 def test_handshake_and_search(self):
  self.assertIn('Fairy-Stockfish',self.e.name);g=Game()
  a=self.e.analyse(g.s,0,nodes=2000,multipv=3)
  self.assertTrue(a);self.assertTrue(all(x.move in g.legal() for x in a));self.assertGreater(max(x.nodes for x in a),0)
 def test_engine_launch_from_directory_with_spaces(self):
  # Regression: SF14 splits absolute `load C:\...\Hastings Chess\hastings.ini`
  # on whitespace, silently ignoring the custom-piece variant. The cwd-relative
  # config name must work even when the executable's own path contains spaces.
  with tempfile.TemporaryDirectory(prefix='Hastings Chess path with spaces ') as temp:
   base=Path(temp);engine_dir=base/'engine';engine_dir.mkdir()
   shutil.copy2(engine_uci.BASE/'engine'/'hastings.ini',engine_dir/'hastings.ini')
   executable=engine_uci.default_engine()
   copied=engine_dir/executable.name
   shutil.copy2(executable,copied)
   with patch.object(engine_uci,'BASE',base):
    e=FairyEngine(path=copied)
    try:
     self.assertIn('Fairy-Stockfish',e.name)
     self.assertTrue(e.analyse(Game().s,0,nodes=1200))
    finally:e.close()
 def test_custom_piece_perft(self):
  for blocker in 'pnbrqPH.':
   pieces={'a1':'K','h8':'k','d4':'H'}
   if blocker!='.':pieces['d6']=blocker
   self.same_moves(position(pieces),0)
 def test_black_pawn_pushed_to_eighth_rank(self):
  self.same_moves(position({'a1':'K','h8':'k','a8':'p'}),1)
 def test_castle_ep_promotion(self):
  s=position({'e1':'K','h1':'R','e8':'k','a7':'P','b4':'H'});s.castle['K']=True
  self.same_moves(s,0)
  s=position({'a1':'K','h8':'k','e5':'P','d5':'p'});s.ep=at('d6');self.same_moves(s,0)
 def test_nonmoving_king_check_is_rejected(self):
  s=position({'a2':'K','h8':'k','b5':'P','h2':'r'})
  self.assertFalse(compatible(s,1))
  with self.assertRaises(IncompatiblePosition):fen(s,1)
 def test_random_differential(self):
  rng=random.Random(501)
  for seed in range(4):
   g=Game(seed,{4:1})
   for ply in range(45):
    g.start_turn()
    if g.winner:break
    if compatible(g.s,g.side):self.same_moves(g.s,g.side)
    g.move(rng.choice(g.legal()))
 def test_hybrid_actual_engine_calls(self):
  g=Game();h=Hybrid(self.e,level=1,nodes=2000)
  m=h.choose(g);self.assertIn(m,g.legal());self.assertGreater(h.last_info['calls'],0)
 def test_compound_unrepresentable_start(self):
  g=Game();g.s=position({'a2':'K','h8':'k','b5':'P','h2':'r','f6':'n'})
  g.side=1;g.phase='response';g.charged=True;g.normal_pending=True;g.bonus_left=2
  h=Hybrid(self.e,level=1,nodes=2000);m=h.choose(g)
  self.assertIn(m,g.legal())
  # A mate can be proved in Python before an endpoint engine call is needed.
  if abs(h.last_info['score_cp'])<90000:self.assertGreater(h.last_info['calls'],0)

 def test_ordinary_mate_in_one(self):
  g=Game();g.s=position({'f6':'K','h8':'k','g6':'Q'});g.attempted_move=1
  h=Hybrid(self.e,level=2,nodes=6000);m=h.choose(g);g.move(m)
  self.assertEqual(g.winner,'white')
 def test_capture_free_queen(self):
  g=Game();g.s=position({'h1':'K','a8':'k','e4':'Q','e8':'r'});g.side=1
  h=Hybrid(self.e,level=2,nodes=6000);m=h.choose(g)
  self.assertEqual(m[:2],(at('e8'),at('e4')))
 def test_search_does_not_peek_or_consume_charge_rng(self):
  g=Game(42);g.white_move=24;g.side=1
  before=g.rng.getstate();h=Hybrid(self.e,level=1,nodes=1000);h.choose(g)
  self.assertEqual(before,g.rng.getstate());self.assertGreater(h.last_info['calls'],1)
 def test_game5_bonus_first_hybrid(self):
  original=json.loads((Path(__file__).parent/'replays/original_game_5.json').read_text())
  g=Game(5,{29:1});g.s=r.state_from_dict(original['events'][56]);g.white_move=29
  g.start_turn();self.assertEqual(g.phase,'rescue_bonus')
  h=Hybrid(self.e,level=1,nodes=1200)
  m=h.choose(g);self.assertIn(m,g.legal());self.assertEqual(uci_move(m),'f8f7')
  g.move(m);self.assertEqual(g.phase,'response')
  m=h.choose(g);self.assertIn(m,g.legal())
if __name__=='__main__':unittest.main()
