"""Native Tk control tests. Requires a real/virtual display, no third-party modules."""
import json,tempfile,time,types,unittest
from pathlib import Path
from unittest.mock import patch
import tkinter as tk
from app import App
from game import Game
from tests import position

class GuiTests(unittest.TestCase):
 def setUp(self):
  self.root=tk.Tk();tk.ttk.Style().theme_use('clam');self.root.geometry('1100x800');self.app=App(self.root)
  self.app.mode.set('Two humans');self.root.update()
 def tearDown(self):self.app.close()
 def click(self,square):
  a=self.app;ox,oy,s=a.geometry;x=ord(square[0])-97;y=int(square[1])-1
  col=7-x if a.flip else x;row=y if a.flip else 7-y
  a.click(types.SimpleNamespace(x=int(ox+(col+.5)*s),y=int(oy+(row+.5)*s)))
 def wait(self,predicate,seconds=8):
  end=time.monotonic()+seconds
  while time.monotonic()<end:
   self.root.update()
   if predicate():return
   time.sleep(.01)
  self.fail('Timed out waiting for GUI worker')
 def test_human_move_flip_undo(self):
  self.click('e2');self.click('e4');self.assertEqual(self.app.g.s.b[28],'P')
  self.app.flip_board();self.assertTrue(self.app.flip)
  self.app.undo();self.assertEqual(self.app.g.s.b[12],'P');self.assertTrue(self.app.paused)
 def test_replay_open_navigation_and_live(self):
  p=Path(__file__).parent/'replays/original_game_1.json'
  with patch('app.filedialog.askopenfilename',return_value=str(p)):self.app.open_replay()
  self.assertEqual(self.app.replay_index,0);self.app.jump_charge();self.assertEqual(self.app.replay_index,47)
  self.app.next();self.assertEqual(self.app.replay_index,48);self.app.previous();self.assertEqual(self.app.replay_index,47)
  self.app.live();self.assertIsNone(self.app.replay)
 def test_save_is_importable(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'save.json'
   with patch('app.filedialog.asksaveasfilename',return_value=str(p)):self.app.save()
   self.assertEqual(json.loads(p.read_text())['format'],'hastings-chess-3')
 def test_no_live_moves_from_old_position(self):
  self.click('e2');self.click('e4');self.app.previous();before=self.app.g.s.b[:]
  self.click('e7');self.click('e5');self.assertEqual(before,self.app.g.s.b)
 def test_promotion_choice(self):
  a=self.app;a.g.s=position({'h1':'K','h8':'k','a7':'P'});a.g.log=[];a.g._record('promotion test','start',[]);a.refresh()
  with patch.object(a,'promotion',return_value='n'):self.click('a7');self.click('a8')
  self.assertEqual(a.g.s.b[56],'N')
 def test_narrow_and_desktop_board_bounds(self):
  for size in ('640x580','1280x900'):
   self.root.geometry(size);self.root.update();x,y,s=self.app.geometry
   self.assertGreater(s,20);self.assertGreaterEqual(x,0);self.assertGreaterEqual(y,0)
   self.assertLessEqual(x+8*s,self.app.canvas.winfo_width())
 def test_real_engine_computer_turn(self):
  a=self.app;a.mode.set('Saxons vs computer');a.level.set(1)
  self.click('e2');self.click('e4')
  self.wait(lambda:a.g.side==0 and a.g.white_move==2)
  self.assertIn('Fairy-Stockfish',a.engine_status.get())
 def test_restart_discards_stale_engine_move(self):
  a=self.app;a.mode.set('Computer vs computer');a.level.set(1);a.pump()
  a.new();a.mode.set('Two humans')
  end=time.monotonic()+.6
  while time.monotonic()<end:self.root.update();time.sleep(.01)
  self.assertEqual(a.g.s.b,Game().s.b)
 def test_engine_failure_stays_visible(self):
  a=self.app;a.mode.set('Computer vs computer')
  with patch('workers.FairyEngine',side_effect=RuntimeError('test engine unavailable')),patch('app.messagebox.showerror') as show:
   a.pump();self.wait(lambda:a.paused)
   self.assertTrue(show.called);self.assertEqual(a.engine_mode.get(),'Fairy-Stockfish hybrid')

 def test_batch_game_selector(self):
  one=Game(10).export();two=Game(11).export()
  self.app.load_replay_data({'format':'hastings-batch-2','games':[{'replay':one},{'replay':two}]})
  self.app.replay_selector.current(1);self.app.choose_replay()
  self.assertEqual(self.app.replay['seed'],11);self.assertEqual(self.app.replay_index,0)
 def test_rules_window_and_standard_ruleset(self):
  a=self.app;before=a.g.export();self.assertFalse(hasattr(a,'rules_box'))
  self.assertEqual(self.root.title(),'Hastings Chess: Catastrophic Military Stupidity Simulator. Also Axes')
  a.rules_button.invoke();self.root.update()
  self.assertTrue(a.rules_window.winfo_exists())
  self.assertIn('and it was Wednesday.',a.rules_window.winfo_children()[0].winfo_children()[1].get('1.0','end'))
  a.rules_window.destroy();a.show_rules();self.root.update()
  self.assertTrue(a.rules_window.winfo_exists());self.assertEqual(a.g.export(),before)
  a.new();self.assertEqual(a.g.bonus_mode,'knight_pawn')
 def test_game5_rescue_click_and_replay(self):
  import rules as r
  from tests import at
  original=json.loads((Path(__file__).parent/'replays/original_game_5.json').read_text())
  a=self.app;a.g=Game(5,{29:1});a.g.s=r.state_from_dict(original['events'][56]);a.g.white_move=29
  a.g.log=[];a.g._record('Before charge','start',[]);a.g.start_turn();a.refresh()
  self.assertEqual(a.g.phase,'rescue_bonus')
  self.click('f8');self.click('f7')
  self.assertEqual(a.g.phase,'response');self.assertEqual(a.g.s.b[at('f7')],'p')
  a.load_replay_data(a.g.export());a.choose_replay();a.jump_charge()
  self.assertEqual(a.replay['format'],'hastings-chess-3')
 def test_no_live_evaluation_even_after_game_until_replay(self):
  a=self.app
  with patch('app.ReplayWorker') as worker:
   a.refresh();worker.assert_not_called()
   self.assertIsNone(a.eval_canvas);self.assertIsNone(a.eval_label)
   a.game_rated=False;a.g._end('white','checkmate');a.refresh()
   worker.assert_not_called()
   self.assertIsNone(a.eval_canvas);self.assertIsNone(a.eval_label)
   a.review_finished();self.assertIsNotNone(a.eval_canvas)
   worker.assert_called_once()
   self.assertIn('Analysing',a.eval_label.cget('text'))
   a.replay_cache[(id(a.replay),a.replay_index)]=(None,'engine delayed')
   a.draw_eval();self.assertIn('unavailable',a.eval_label.cget('text'))
   a.live();self.assertIsNone(a.eval_canvas);self.assertIsNone(a.eval_label)
 def test_difficulty_persists_and_ratings_result_only(self):
  from settings import Settings
  a=self.app
  with tempfile.TemporaryDirectory() as d:
   a.settings=Settings(Path(d)/'settings.json');a.level_text.set('7. Expert');a.difficulty_changed()
   self.assertEqual(Settings(a.settings.path).data['difficulty'],7)
   a.mode.set('Computer vs computer');a.mode_changed();a.g._end('black','checkmate');a.refresh()
   self.assertEqual(Settings(a.settings.path).norman_elo,1066)
   a.new();a.mode.set('Two humans');a.mode_changed();a.game_rated=True
   a.g._end('black','checkmate');a.refresh()
   self.assertGreater(Settings(a.settings.path).norman_elo,1066)
   self.assertIn('1066 → 1066 (+0)',a.rating_detail.cget('text'))

if __name__=='__main__':unittest.main()
