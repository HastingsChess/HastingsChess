import unittest
from unittest.mock import patch
import random
import rules as r
from game import Game,replay_valid
from ai import Search

def blank():
 s=r.State();s.b=['.']*64;s.b[4]='K';s.b[60]='k';return s

class Rules(unittest.TestCase):
 def test_start_and_piece_count(self):
  s=r.State();self.assertEqual(s.b.count('H'),2);self.assertEqual(s.b.count('P'),6)
  self.assertEqual(len([p for p in s.b if p!='.']),32)
 def test_housecarl_no_two_capture_or_jump(self):
  s=blank();s.b[27]='H';s.b[45]='n';s.b[28]='p'
  moves=r.legal(s,0);self.assertFalse(any(m[0]==27 and m[1]==45 for m in moves))
  self.assertTrue(any(m[0]==27 and m[1]==28 for m in moves))
  self.assertTrue(r.attacked(28,0,s.b));self.assertFalse(r.attacked(45,0,s.b))
 def test_charge_order_and_push_identity(self):
  s=blank();s.b[r.sq(0,1)]='P';s.b[r.sq(0,2)]='P'
  _,events=r.charge(s)
  self.assertEqual([e['from'] for e in events],['a3','a2'])
  self.assertEqual(s.b[r.sq(0,5)],'P')
  self.assertEqual(s.b[r.sq(0,4)],'P')
 def test_blocked_capture_and_kings(self):
  s=blank();s.b[8]='H';s.b[16]='p';s.b[24]='n';r.charge(s)
  self.assertEqual(s.b[16],'H');self.assertEqual(s.b[24],'n')
  s=blank();s.b[52]='P';r.charge(s);self.assertEqual(s.b[60],'k')
 def test_promotions(self):
  s=blank();s.b[48]='P';self.assertEqual({m[2] for m in r.legal(s,0) if m[0]==48},set('qrbn'))
  r.charge(s);self.assertEqual(s.b[56],'H')
  s=blank();s.b[48]='P';s.b[56]='r';r.charge(s)
  self.assertEqual(s.b[56],'H');self.assertEqual(s.b[48],'.')
 def test_castle_and_en_passant(self):
  s=blank();s.b[7]='R';self.assertTrue(any(m[3]=='castle' for m in r.legal(s,0)))
  s=blank();s.b[36]='P';s.b[35]='p';s.ep=43
  self.assertTrue(any(m[3]=='ep' for m in r.legal(s,0)))
  m=next(m for m in r.legal(s,0) if m[3]=='ep');r.apply(s,m)
  self.assertEqual(s.b[35],'.')
 def test_pushed_rook_castle_right(self):
  s=blank();s.b[56]='r';s.b[48]='P';r.charge(s)
  self.assertFalse(s.castle['q'])
 def test_repeat_hazard_only_once(self):
  g=Game(3,{20:0});g.white_move=20
  g.start_turn();state=g.rng.getstate();g.start_turn()
  self.assertEqual(g.rng.getstate(),state)
  g.hazard={20:1};g.attempted_move=None;g.start_turn()
  self.assertTrue(g.charged);self.assertIn(g.phase,('bonus','response','rescue_bonus'))
 def test_bonus_two_actions_same_knight(self):
  g=Game();g.s=blank();g.s.b[57]='n';g.s.b[8]='P';g.s.b[15]='H'
  g.phase='response';g.charged=True;g.side=1;g.normal_pending=True;g.bonus_left=2
  normal=next(m for m in g.legal() if m[0]==57)
  g.move(normal);self.assertEqual(g.bonus_left,2)
  a=next(m for m in g.legal() if m[0]==normal[1]);g.move(a)
  self.assertEqual(g.bonus_left,1)
  b=next(m for m in g.legal() if m[0]==a[1]);g.move(b)
  self.assertEqual(g.bonus_left,0);self.assertEqual(g.side,0)
 def test_ai_and_replay(self):
  g=Game();m=Search(1,.2).choose(g);self.assertIn(m,g.legal())
  self.assertEqual(len(replay_valid(g.export())['events']),1)



# Phase-two regressions. The original ten tests above remain in the suite.
from pathlib import Path
import json

def position(pieces):
 s=r.State();s.b=['.']*64;s.castle=dict.fromkeys('KQkq',False)
 for square,p in pieces.items():s.b[(int(square[1])-1)*8+ord(square[0])-97]=p
 return s

def at(square):return (int(square[1])-1)*8+ord(square[0])-97

def destinations(s,square,side=0):return {r.symbol(m[1]) for m in r.legal(s,side) if m[0]==at(square)}

class PhaseTwoRules(unittest.TestCase):
 def test_housecarl_all_empty_moves(self):
  s=position({'a1':'K','h8':'k','d4':'H'})
  self.assertEqual(destinations(s,'d4'),set('c3 d3 e3 c4 e4 c5 d5 e5'.split()))
 def test_housecarl_adjacent_capture_all_directions(self):
  for square in 'c3 d3 e3 c4 e4 c5 d5 e5'.split():
   s=position({'a1':'K','h8':'k','d4':'H',square:'n'})
   self.assertIn(square,destinations(s,'d4'))
 def test_housecarl_two_orthogonal_captures_forbidden(self):
  for square in 'b4 f4 d2 d6'.split():
   s=position({'a1':'K','h8':'k','d4':'H',square:'n'})
   self.assertNotIn(square,destinations(s,'d4'))
 def test_housecarl_cannot_jump_or_move_two_diagonal(self):
  s=position({'a1':'K','h8':'k','d4':'H','d5':'P','c4':'p'})
  for square in 'd6 b4 b2 f2 b6 f6'.split():self.assertNotIn(square,destinations(s,'d4'))
 def test_housecarl_can_enter_attack(self):
  s=position({'a1':'K','h8':'k','d4':'H','e8':'r'})
  self.assertIn('e4',destinations(s,'d4'));self.assertTrue(r.attacked(at('e4'),1,s.b))
 def test_charge_housecarl_distant_blocker_not_captured(self):
  s=position({'a1':'K','h8':'k','d3':'H','d5':'p','d6':'n'})
  _,ev=r.charge(s)
  self.assertEqual(s.b[at('d4')],'H');self.assertEqual(s.b[at('d5')],'p')
  self.assertEqual(ev[0]['event'],'blocked by housecarl capture range')
 def test_charge_housecarl_distant_blocker_may_push(self):
  s=position({'a1':'K','h8':'k','d3':'H','d5':'p'})
  r.charge(s);self.assertEqual(s.b[at('d5')],'H');self.assertEqual(s.b[at('d6')],'p')
 def test_charge_housecarl_adjacent_blocker_capture(self):
  s=position({'a1':'K','h8':'k','d3':'H','d4':'p','d5':'n'})
  r.charge(s);self.assertEqual(s.b[at('d4')],'H');self.assertEqual(s.b.count('p'),0)
 def test_replay_one_regression(self):
  d=json.loads((Path(__file__).parent/'replays/original_game_1.json').read_text())
  pre=d['events'][47];s=r.state_from_dict(pre)
  _,events=r.charge(s)
  e=next(e for e in events if e['from']=='d3')
  self.assertEqual(e['to'],'d4');self.assertEqual(s.b[at('d5')],'p')
 def test_pawn_captures_third_square_when_push_blocked(self):
  s=position({'a1':'K','h8':'k','d2':'P','d5':'p','d6':'n'})
  r.charge(s);self.assertEqual(s.b[at('d5')],'P');self.assertEqual(s.b.count('p'),0)
 def test_friend_and_king_blockers_never_captured(self):
  s=position({'a1':'K','d5':'k','d2':'P','e2':'H','e3':'B','e4':'R'})
  before=s.b.count('B');r.charge(s)
  self.assertEqual(s.b[at('d4')],'P');self.assertEqual(s.b[at('d5')],'k');self.assertEqual(s.b.count('B'),before)
 def test_charge_exposes_check_without_mate(self):
  s=position({'a2':'K','h8':'k','b2':'P','h2':'r'})
  self.assertFalse(r.in_check(s,0));r.charge(s)
  self.assertEqual(s.b[at('b5')],'P');self.assertTrue(r.in_check(s,0));self.assertTrue(r.legal(s,0))
 def test_charge_checkmate_exemption_real_position(self):
  s=position({'a2':'K','c4':'k','b2':'P','h2':'r','h1':'r','c5':'b','f8':'N'})
  self.assertFalse(r.in_check(s,0));self.assertTrue(r.legal(s,0))
  t=s.copy();t.b[at('b2')]='.';t.b[at('b5')]='P'
  self.assertTrue(r.in_check(t,0));self.assertFalse(r.legal(t,0))
  _,ev=r.charge(s)
  self.assertEqual(s.b[at('b2')],'P');self.assertEqual(ev[0]['event'],'checkmate exemption')
 def test_charge_starting_in_check(self):
  s=position({'a2':'K','h8':'k','b2':'P','a8':'r'})
  self.assertTrue(r.in_check(s,0));r.charge(s)
  self.assertEqual(s.b[at('b5')],'P');self.assertTrue(r.in_check(s,0))
 def test_expired_ep_not_an_escape(self):
  s=position({'a1':'K','h8':'k','e5':'P','d5':'p'});s.ep=at('d6')
  r.charge(s);self.assertEqual(s.ep,-1)
 def test_trace_intermediate_board_and_rights(self):
  s=position({'a1':'K','h8':'k','a6':'P','a7':'r','b2':'P'});s.castle['q']=True
  trace=[];r.charge(s,trace)
  self.assertEqual(trace[0]['board'][at('b2')],'P')
  self.assertEqual(trace[-1]['board'][at('b5')],'P')
 def test_black_promotions_standard(self):
  s=position({'h1':'K','h8':'k','a2':'p'})
  self.assertEqual({m[2] for m in r.legal(s,1) if m[0]==at('a2')},set('qrbn'))
 def test_normal_king_safety(self):
  s=position({'a2':'K','h8':'k','b2':'P','h2':'r'})
  self.assertFalse(any(m[0]==at('b2') for m in r.legal(s,0)))
 def test_friendly_push_identity_not_duplicated(self):
  s=position({'a1':'K','h8':'k','b2':'P','b3':'H','b5':'B'})
  before=len([p for p in s.b if p!='.']);_,ev=r.charge(s)
  self.assertEqual(len([p for p in s.b if p!='.']),before)
  self.assertEqual(len(ev),2);self.assertEqual(len({e['from'] for e in ev}),2)

 def test_front_unit_pushed_after_it_already_charged(self):
  s=position({'a1':'K','h8':'k','b2':'P','b3':'H'})
  _,ev=r.charge(s)
  self.assertEqual(s.b[at('b6')],'H');self.assertEqual(s.b[at('b5')],'P')
  self.assertEqual(len(ev),2);self.assertEqual(s.b.count('H'),1)

class ControllerTests(unittest.TestCase):
 def test_default_hazard_exact(self):
  self.assertEqual(r.CHARGE_HAZARD,{20:.01,21:.03,22:.05,23:.07,24:.09,25:.1,26:.15,27:.25,28:.4,29:.6,30:1})
 def test_only_one_failed_draw(self):
  g=Game(1,{20:.0001});g.white_move=20;g.start_turn()
  a=g.rng.getstate();g.start_turn();self.assertEqual(a,g.rng.getstate());self.assertFalse(g.charged)
 def test_guaranteed_move30_once(self):
  g=Game();g.white_move=30;g.start_turn();self.assertTrue(g.charged)
  b=g.s.b[:];g.start_turn();self.assertEqual(b,g.s.b)
 def test_move_cannot_bypass_charge(self):
  g=Game();g.white_move=30;m=g.legal()[0]
  with self.assertRaises(ValueError):g.move(m)
  self.assertTrue(g.charged)
 def test_no_knights_skips_and_resumes(self):
  g=Game();g.s=position({'a1':'K','h8':'k','a2':'P'});g.phase='response';g.side=1;g.charged=True;g.normal_pending=True;g.bonus_left=2
  g.move(g.legal()[0]);self.assertEqual(g.side,0);self.assertEqual(g.bonus_left,0)
  self.assertEqual(sum(e.get('skipped',False) for e in g.log),2)
 def test_pinned_knight_bonus_illegal(self):
  s=position({'a1':'K','e8':'k','e7':'n','e1':'R'})
  self.assertEqual(r.legal(s,1,True),[])
 def test_mate_on_ordinary_response_stops_bonus(self):
  g=Game();g.s=position({'a1':'K','c3':'k','b3':'q','h8':'n'});g.phase='response';g.side=1;g.charged=True;g.normal_pending=True;g.bonus_left=2
  m=next(m for m in g.legal() if m[0]==at('b3') and m[1]==at('b2'))
  g.move(m);self.assertEqual(g.winner,'black');self.assertFalse(any(e['phase']=='bonus' for e in g.log))
 def test_undo_restores_rng_and_charge(self):
  g=Game(1,{1:1});before=g.rng.getstate();g.start_turn();board=g.s.b[:]
  g.undo();self.assertFalse(g.charged);self.assertEqual(g.rng.getstate(),before)
  g.start_turn();self.assertEqual(g.s.b,board)
 def test_metadata_after_move_and_export(self):
  g=Game();g.move(g.legal()[0]);self.assertEqual(g.log[-1]['side'],1)
  self.assertEqual(replay_valid(json.loads(json.dumps(g.export())))['ruleset'],r.RULESET+'-knight_pawn')
 def test_old_replays_stay_viewable(self):
  for i in (1,2):
   d=json.loads((Path(__file__).parent/f'replays/original_game_{i}.json').read_text());replay_valid(d)
 def test_empty_replay_rejected(self):
  with self.assertRaises(ValueError):replay_valid({'format':'hastings-chess-2','events':[]})
 def test_random_play_piece_and_king_invariants(self):
  rng=random.Random(98)
  for seed in range(5):
   g=Game(seed,{3:1});previous=32
   for ply in range(60):
    g.start_turn()
    if g.winner:break
    moves=g.legal();self.assertTrue(moves);g.move(rng.choice(moves))
    count=sum(p!='.' for p in g.s.b);self.assertLessEqual(count,previous);previous=count
    self.assertEqual(g.s.b.count('K'),1);self.assertEqual(g.s.b.count('k'),1)


class PhaseThreeRules(unittest.TestCase):
 def test_housecarl_exactly_nonroyal_king(self):
  s=position({'a1':'K','h8':'k','d4':'H'})
  self.assertEqual(destinations(s,'d4'),set('c3 d3 e3 c4 e4 c5 d5 e5'.split()))
  for target in 'b4 f4 d2 d6 b2 f2 b6 f6'.split():self.assertNotIn(target,destinations(s,'d4'))
  s=position({'a1':'K','h8':'k','d4':'H','e4':'n','e8':'r'})
  self.assertIn('e4',destinations(s,'d4'))
 def test_housecarl_charge_still_two_without_long_capture(self):
  s=position({'a1':'K','h8':'k','d3':'H','d5':'p','d6':'n'})
  r.charge(s);self.assertEqual(s.b[at('d4')],'H');self.assertEqual(s.b[at('d5')],'p')
 def test_bonus_pawn_advance_diagonal_and_forward_capture(self):
  s=position({'a1':'K','h8':'k','d6':'p','d5':'P','e5':'H'})
  d={r.symbol(m[1]):m for m in r.legal(s,1,bonus_mode='knight_pawn') if m[0]==at('d6')}
  self.assertEqual(set(d),{'d5','e5'});self.assertEqual(d['d5'][3],'bonus_forward_capture')
  s.b[at('d5')]='.'
  self.assertIn('d5',{r.symbol(m[1]) for m in r.legal(s,1,bonus_mode='knight_pawn') if m[0]==at('d6')})
 def test_bonus_pawn_restrictions(self):
  s=position({'h1':'K','h8':'k','a7':'p','b5':'p','c5':'P','d2':'p','e2':'P'})
  s.ep=at('d4')
  moves=r.legal(s,1,bonus_mode='knight_pawn')
  self.assertFalse(any(m[0]==at('a7') and m[1]==at('a5') for m in moves))
  self.assertFalse(any(m[0]==at('d2') and m[1]==at('d1') for m in moves))
  self.assertFalse(any(m[3]=='double' or m[3]=='ep' or m[2] for m in moves))
  self.assertFalse(any(m[0]==at('b5') and m[1]==at('d4') for m in moves))
 def test_bonus_same_pawn_twice(self):
  g=Game(bonus_mode='knight_pawn');g.s=position({'a1':'K','h8':'k','d6':'p'})
  g.side=1;g.charged=True;g.phase='response';g.normal_pending=True;g.bonus_left=2
  g.move(next(m for m in g.legal() if m[0]==at('h8')))
  g.move(next(m for m in g.legal() if m[0]==at('d6') and m[1]==at('d5')))
  g.move(next(m for m in g.legal() if m[0]==at('d5') and m[1]==at('d4')))
  self.assertEqual(g.s.b[at('d4')],'p');self.assertEqual(g.side,0)
 def test_legacy_unrestricted_rejected(self):
  with self.assertRaisesRegex(ValueError,'Unsupported pre-release experimental'):
   Game(bonus_mode='any_piece')
  with self.assertRaisesRegex(ValueError,'Unsupported pre-release experimental'):
   r.legal(position({'h1':'K','h8':'k'}),1,bonus_mode='any_piece')
  data=Game().export();data['bonus_mode']='any_piece'
  with self.assertRaisesRegex(ValueError,'Unsupported pre-release experimental'):
   replay_valid(data)
  data=Game().export();data['ruleset']='hastings-any_piece'
  with self.assertRaisesRegex(ValueError,'Unsupported pre-release experimental'):
   replay_valid(data)
 def test_game5_rescue_bonus_first_then_ordinary_and_bonus(self):
  data=json.loads((Path(__file__).parent/'replays/original_game_5.json').read_text())
  before=data['events'][56]
  g=Game(seed=5,hazard={29:1},bonus_mode='knight_pawn');g.s=r.state_from_dict(before)
  g.white_move=29;g.side=0;g.log=[];g._record('Before game 5 charge','start',[])
  g.start_turn()
  self.assertIsNone(g.winner);self.assertEqual(g.phase,'rescue_bonus')
  self.assertEqual(r.legal(g.s,1),[])
  bonus=g.legal();self.assertEqual({(r.symbol(m[0]),r.symbol(m[1])) for m in bonus},{('f8','f7')})
  g.move(bonus[0]);self.assertFalse(r.in_check(g.s,1));self.assertEqual(g.phase,'response');self.assertEqual(g.bonus_left,1)
  g.move(g.legal()[0]);self.assertEqual(g.phase,'bonus')
  g.move(g.legal()[0]);self.assertEqual(g.side,0)
  replay_valid(json.loads(json.dumps(g.export())))
  self.assertEqual([e['phase'] for e in g.log if e['phase'] in ('rescue_bonus','response','bonus')][:3],['rescue_bonus','response','bonus'])
 def test_view_all_previous_rule_versions(self):
  for i in (1,2,3,4,5):
   d=json.loads((Path(__file__).parent/f'replays/original_game_{i}.json').read_text())
   replay_valid(d)

if __name__=='__main__':unittest.main()
