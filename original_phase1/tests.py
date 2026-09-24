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
  self.assertTrue(g.charged);self.assertEqual(g.phase,'bonus' if not g.legal() else 'response')
 def test_bonus_two_actions_same_knight(self):
  g=Game();g.s=blank();g.s.b[57]='n';g.s.b[8]='P';g.s.b[15]='H'
  g.phase='response';g.charged=True;g.side=1
  normal=next(m for m in g.legal() if m[0]==57)
  g.move(normal);self.assertEqual(g.bonus_left,2)
  a=next(m for m in g.legal() if m[0]==normal[1]);g.move(a)
  self.assertEqual(g.bonus_left,1)
  b=next(m for m in g.legal() if m[0]==a[1]);g.move(b)
  self.assertEqual(g.bonus_left,0);self.assertEqual(g.side,0)
 def test_ai_and_replay(self):
  g=Game();m=Search(1,.2).choose(g);self.assertIn(m,g.legal())
  self.assertEqual(len(replay_valid(g.export())['events']),1)

if __name__=='__main__':unittest.main()
