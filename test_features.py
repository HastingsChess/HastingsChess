"""Phase-four ratings, replay analysis and ten-level real-engine regressions."""
import json,tempfile,unittest,hashlib,random,math
from pathlib import Path
from unittest.mock import patch
import rules as r
from game import Game
from engine_uci import FairyEngine,compatible
from hybrid import Hybrid,LEVELS,OLD_LEVELS,SEARCH_LEVEL,BENCHMARK_LEVEL_3,CURRENT_BUILD_LEVEL_1,WEAK_TOLERANCE
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
   self.assertEqual((s.norman_elo,s.data['difficulty']),(1066,3))
   self.assertEqual(s.record('one','black'),(1066,norman_next(1066,1)))
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
   p=Path(d)/'bad.json';p.write_text('{bad');self.assertEqual(Settings(p).norman_elo,1066)
 def test_legacy_migration_once(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'settings.json';p.write_text(json.dumps({'norman_elo':1100,'difficulty':7,'rated_games':['old']}))
   s=Settings(p);self.assertEqual((s.norman_elo,s.data['difficulty']),(1066,7))
   self.assertEqual(s.data['schema_version'],2)
   s.record('release-win','black');self.assertEqual(Settings(p).norman_elo,1082)

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

class DifficultyCalibrationTests(unittest.TestCase):
 def test_fallible_selection_remains_legal_and_weaker(self):
  # Same plausible, already Hastings-legal candidates at many move numbers.
  # Deterministic per position: repeat runs cannot change a saved benchmark.
  g=Game();ranked=[(0,g.legal()[0]),(-80,g.legal()[1]),(-180,g.legal()[2]),(-420,g.legal()[3])]
  scores={}
  for level in (1,2,3,4):
   h=Hybrid(engine=object(),level=level)
   values=[]
   for move_number in range(1,201):
    g.white_move=move_number
    picked=h._select(ranked,g)
    self.assertIn(picked[1],g.legal())
    self.assertEqual(picked,h._select(ranked,g))
    values.append(picked[0])
   scores[level]=sum(values)
  self.assertLess(scores[1],scores[2]);self.assertLess(scores[2],scores[3]);self.assertLess(scores[3],scores[4])
  self.assertLess(scores[1],scores[4]-1000)
  self.assertLess(scores[1],0)
 def test_current_level_one_is_exactly_public_four_including_choices(self):
  h=Hybrid(engine=object(),level=4);g=Game()
  self.assertEqual((h.level,h.seconds,h.candidates,h.base_nodes),(1,.10,2,250))
  self.assertEqual(WEAK_TOLERANCE[4],250)
  ranked=[(30,g.legal()[0]),(-170,g.legal()[1])]
  for n in range(1,80):
   g.white_move=n
   digest=hashlib.sha256((''.join(g.s.b)+str(g.white_move)+g.phase+'1').encode()).digest()
   expected=random.Random(int.from_bytes(digest[:8],'big')).choices(ranked,
            weights=[1,math.exp(-200/250)],k=1)[0]
   self.assertEqual(h._select(ranked,g),expected)
 def test_ordinary_and_compound_weakness_uses_legal_candidates(self):
  from unittest.mock import patch
  from types import SimpleNamespace
  fake=SimpleNamespace(calls=0,total_nodes=0,name='test')
  ordinary=Game();ordinary.charged=True
  moves=ordinary.legal()[:4]
  answers=[SimpleNamespace(cp=cp,move=m,mate=None,pv=[]) for cp,m in zip((0,-80,-180,-420),moves)]
  for level in (1,2,3,4):
   h=Hybrid(fake,level=level)
   with patch.object(h,'_analyse',return_value=answers):
    self.assertIn(h.choose(ordinary),ordinary.legal())
  response=Game(hazard={1:1});response.start_turn();self.assertEqual(response.phase,'response')
  options=[(cp,[m]) for cp,m in zip((0,-80,-180,-420),response.legal()[:4])]
  scores={}
  for level in (1,2,3,4):
   h=Hybrid(fake,level=level);values=[]
   for n in range(1,80):
    response.white_move=n
    with patch.object(h,'_compound',return_value=options) as compound:
     move=h.choose(response)
    self.assertIn(move,response.legal())
    self.assertTrue(compound.call_args.kwargs['alternatives'])
    values.append(h.last_info['score_cp'])
   scores[level]=sum(values)
  self.assertLess(scores[1],scores[2]);self.assertLess(scores[2],scores[3]);self.assertLess(scores[3],scores[4])
 def test_benchmark_configuration_and_simulation_entry(self):
  from simulate import run
  h=Hybrid(engine=object(),level=BENCHMARK_LEVEL_3)
  self.assertEqual((h.level,h.seconds,h.candidates,h.base_nodes),(3,1.6,5,10000))
  with self.assertRaisesRegex(ValueError,'requires Fairy-Stockfish'):
   run(1,1,1,level=BENCHMARK_LEVEL_3,white='light',black='fairy')
  public=run(1,1,1,level=3,white='light',black='light')
  self.assertEqual((public['settings']['level'],public['settings']['difficulty_preset']),(3,'public'))

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
 def test_safe_unrepresentable(self):
  from tests import position
  g=Game();g.s=position({'a2':'K','h8':'k','b5':'P','h2':'r','f6':'n'})
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
  self.assertEqual(LEVELS[4],CURRENT_BUILD_LEVEL_1)
  self.assertEqual(LEVELS[10],OLD_LEVELS[10])
  self.assertEqual(OLD_LEVELS[3],(1.6,5,10000))
  self.assertEqual([LEVELS[n][1] for n in (1,2,3,4)],[6,5,4,2])
  self.assertEqual([WEAK_TOLERANCE[n] for n in (1,2,3,4)],[700,430,300,250])
  self.assertTrue(all(LEVELS[n][0]<LEVELS[n+1][0] for n in (1,2,3)))
  for prev,nxt in zip(list(LEVELS.values())[3:],list(LEVELS.values())[4:]):
   self.assertTrue(all(b>a for a,b in zip(prev,nxt)))
  benchmark=Hybrid(self.e,level=BENCHMARK_LEVEL_3)
  self.assertEqual((benchmark.level,benchmark.seconds,benchmark.candidates,benchmark.base_nodes),(3,*OLD_LEVELS[3]))
  self.assertEqual(Hybrid(self.e,level=4).level,1)
  self.assertNotEqual(Hybrid(self.e,level=3).level,benchmark.level)
  for level in LEVELS:
   h=Hybrid(self.e,level=level,nodes=350)
   normal=Game();m=h.choose(normal);self.assertIn(m,normal.legal())
   rescue=self.game5();m=h.choose(rescue);self.assertIn(m,rescue.legal())
   rescue.move(m);self.assertEqual(rescue.phase,'response')
   m=h.choose(rescue);self.assertIn(m,rescue.legal())

if __name__=='__main__':unittest.main()
