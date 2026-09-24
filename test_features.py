"""Phase-four ratings, replay analysis and ten-level real-engine regressions."""
import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import rules as r
from game import Game
from engine_uci import FairyEngine,compatible
from hybrid import Hybrid,LEVELS
from replay_analysis import ReplayAnalyzer,Score,display,white_fraction
from settings import Settings,SAXON_RATING,norman_next,settings_path

class RatingsTests(unittest.TestCase):
 def test_initial_expected_and_fixed_saxon(self):
  self.assertEqual(SAXON_RATING,1066)
  expected=1/(1+10**((1066-1100)/400))
  self.assertEqual(norman_next(1100,1),int(1100+32*(1-expected)+.5))
  self.assertEqual(norman_next(1100,0),int(1100-32*expected+.5))
  self.assertEqual(norman_next(1100,.5),int(1100+32*(.5-expected)+.5))
 def test_persistent_and_idempotent(self):
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/'settings.json';s=Settings(path)
   self.assertEqual((s.norman_elo,s.data['difficulty']),(1100,3))
   self.assertEqual(s.record('one','black'),(1100,norman_next(1100,1)))
   self.assertIsNone(Settings(path).record('one','black'))
   s=Settings(path);s.set_difficulty(10)
   self.assertEqual(Settings(path).data['difficulty'],10)
   self.assertEqual(SAXON_RATING,1066)
   with self.assertRaises(ValueError):s.record('aborted',None)
   self.assertEqual(Settings(path).norman_elo,s.norman_elo)
 def test_writable_location_and_corrupt_settings(self):
  with tempfile.TemporaryDirectory() as d:
   with patch('settings.sys.platform','win32'),patch.dict('settings.os.environ',{'APPDATA':d}):
    self.assertEqual(settings_path(),Path(d)/'Hastings Chess'/'settings.json')
   p=Path(d)/'bad.json';p.write_text('{bad');self.assertEqual(Settings(p).norman_elo,1100)

class ReplayScoreTests(unittest.TestCase):
 def test_orientation_and_mate_format(self):
  self.assertEqual(display(Score(125)),'+1.25')
  self.assertEqual(display(Score(-240)),'-2.40')
  self.assertEqual(display(Score(0)),'0.00')
  self.assertEqual(display(Score(99999,3)),'M3')
  self.assertEqual(display(Score(-99999,-2)),'-M2')
  self.assertEqual(display(Score(-100000,0)),'-M0')
  self.assertLess(white_fraction(Score(mate_white=-2)),.5)
  self.assertGreater(white_fraction(Score(125)),.5)
  self.assertLess(white_fraction(Score(-240)),.5)
  self.assertGreaterEqual(white_fraction(Score(1000000)),.02)
  self.assertLessEqual(white_fraction(Score(1000000)),.98)
 def test_old_rules_declined_without_engine_call(self):
  d=json.loads((Path(__file__).parent/'replays/original_game_5.json').read_text())
  with patch('replay_analysis.Hybrid') as hybrid:
   self.assertIsNone(ReplayAnalyzer(None).event(d,0))
   hybrid.assert_called_once() # construction, not search
 def test_certain_charge_preview_replaces_ordinary_score(self):
  from types import SimpleNamespace
  g=Game(1,{30:1});g.white_move=30;g.log=[];g._record('White approaches move 30','start',[])
  fake=SimpleNamespace(analyse=lambda *a,**k:[SimpleNamespace(cp=30,mate=None)])
  analyzer=ReplayAnalyzer(fake)
  with patch.object(analyzer.hybrid,'_charge_value',return_value=300):
   score=analyzer.event(g.export(),0)
  self.assertEqual(score.cp_white,300)
  self.assertIn('100%',score.note)

class RealReplayTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.e=FairyEngine()
 @classmethod
 def tearDownClass(cls):cls.e.close()
 def test_ordinary_move_and_side_perspective(self):
  g=Game();g.move(next(m for m in g.legal() if r.symbol(m[0])=='e2' and r.symbol(m[1])=='e4'))
  d=g.export();a=ReplayAnalyzer(self.e,nodes=1200)
  score=a.event(d,len(d['events'])-1)
  native=self.e.analyse(g.s,1,nodes=1200)[0]
  self.assertEqual(score.cp_white>0,native.cp<0)
  self.assertLess(abs(score.cp_white+native.cp),150)
 def game5(self):
  data=json.loads((Path(__file__).parent/'replays/original_game_5.json').read_text())
  g=Game(5,{29:1});g.s=r.state_from_dict(data['events'][56]);g.white_move=29
  g.log=[];g._record('Before Game 5 charge','start',[]);g.start_turn()
  return g
 def test_charge_and_every_response_action(self):
  g=self.game5();self.assertEqual(g.phase,'rescue_bonus')
  g.move(g.legal()[0]);self.assertEqual(g.phase,'response')
  g.move(g.legal()[0]);self.assertEqual(g.phase,'bonus')
  if g.legal():g.move(g.legal()[0])
  d=g.export();a=ReplayAnalyzer(self.e,nodes=1000)
  for i,event in enumerate(d['events']):
   if event['phase'] in ('charge_end','rescue_bonus','response','bonus','counter_end'):
    score=a.event(d,i)
    self.assertIsInstance(score,Score,(i,event['phase']))
  self.assertIn('compound',a.event(d,next(i for i,e in enumerate(d['events']) if e['phase']=='charge_end')).note)
 def test_safe_unrepresentable_and_unrestricted(self):
  from tests import position
  g=Game(bonus_mode='any_piece');g.s=position({'a2':'K','h8':'k','b5':'P','h2':'r','f6':'n'})
  g.side=1;g.phase='response';g.charged=True;g.normal_pending=True;g.bonus_left=2
  self.assertFalse(compatible(g.s,g.side))
  g.log=[];g._record('post-charge','charge_end',[])
  score=ReplayAnalyzer(self.e,nodes=1000).event(g.export(),0)
  self.assertIsInstance(score,Score)
 def test_both_bonus_steps_in_normal_order(self):
  g=Game(9,{1:1});g.start_turn();self.assertEqual(g.phase,'response')
  for _ in range(3):
   if g.side==0 or g.winner:break
   g.move(g.legal()[0])
  d=g.export();phases=[e['phase'] for e in d['events']]
  self.assertIn('response',phases);self.assertGreaterEqual(phases.count('bonus'),2)
  analyzer=ReplayAnalyzer(self.e,nodes=1000)
  for i,e in enumerate(d['events']):
   if e['phase'] in ('charge_end','response','bonus','counter_end'):
    self.assertIsInstance(analyzer.event(d,i),Score)
 def test_all_levels_legal_ordinary_and_rescue(self):
  self.assertEqual(set(LEVELS),set(range(1,11)))
  self.assertEqual(LEVELS[3],(1.6,5,10000))
  for prev,nxt in zip(LEVELS.values(),list(LEVELS.values())[1:]):
   self.assertTrue(all(b>a for a,b in zip(prev,nxt)))
  for level in LEVELS:
   h=Hybrid(self.e,level=level,nodes=350)
   normal=Game();m=h.choose(normal);self.assertIn(m,normal.legal())
   rescue=self.game5();m=h.choose(rescue);self.assertIn(m,rescue.legal())
   rescue.move(m);self.assertEqual(rescue.phase,'response')
   m=h.choose(rescue);self.assertIn(m,rescue.legal())

if __name__=='__main__':unittest.main()
