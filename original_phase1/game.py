"""Interactive Hastings turn controller and reproducible saved-game format."""
import copy
import random
from collections import Counter
import rules as r

class Game:
    def __init__(self, seed=1, hazard=None):
        self.seed=int(seed); self.rng=random.Random(self.seed)
        self.hazard=dict(r.CHARGE_HAZARD if hazard is None else hazard)
        self.s=r.State(); self.side=0; self.white_move=1
        self.charged=False; self.phase='ordinary'; self.bonus_left=0; self.attempted_move=None
        self.winner=None; self.reason=''; self.history=[]; self.log=[]
        self._record('The Saxons assemble. Nothing could possibly go wrong.', 'start', [])

    def _record(self, label, phase, squares):
        self.log.append(dict(label=label, phase=phase, squares=squares,
            board=''.join(self.s.b), side=self.side, move=self.white_move,
            bonus=self.bonus_left, charged=self.charged, castle=self.s.castle.copy(),
            ep=self.s.ep, hm=self.s.hm, result=self.winner, reason=self.reason))

    def _save(self):
        self.history.append((self.s.copy(),self.side,self.white_move,self.charged,
            self.phase,self.bonus_left,self.winner,self.reason,self.attempted_move,self.rng.getstate(),len(self.log)))

    def undo(self):
        if not self.history:return False
        (self.s,self.side,self.white_move,self.charged,self.phase,self.bonus_left,
         self.winner,self.reason,self.attempted_move,rs,n)=self.history.pop()
        self.rng.setstate(rs);self.log=self.log[:n]
        return True

    def odds(self):return self.hazard.get(self.white_move,0) if self.side==0 and not self.charged else 0

    def legal(self):
        return [] if self.winner else r.legal(self.s,self.side,self.phase=='bonus')

    def _terminal(self, side):
        z=r.turn_terminal(self.s,side)
        if z:
            self.winner=z;self.reason='stalemate' if z=='draw' else 'checkmate'
        elif self.s.hm>=100:
            self.winner='draw';self.reason='fifty-move rule'
        if self.winner:self._record(f'Game over: {self.reason} ({self.winner})','end',[])

    def start_turn(self):
        if self.winner:return
        if self.side!=0 or self.charged or not self.odds() or self.attempted_move==self.white_move:return
        # Game-over takes priority over a new charge draw.
        self._terminal(0)
        if self.winner:return
        self._save()
        self.attempted_move=self.white_move
        if self.rng.random()>=self.odds():
            self.history.pop()
            return
        self.charged=True;self.phase='charge'
        self._record(f'{self.white_move}. THE SAXON CHARGE! The dice hate somebody.', 'charge', [])
        trace=[];_,events=r.charge(self.s,trace,turn=self.white_move)
        for t in trace:
            self._record(t['label'],'charge',t['squares'])
            self.log[-1]['board']=t['board']
        self.s.ep=-1
        self.phase='response';self.side=1
        # The charging turn may end with a Norman checkmate in unusual positions.
        if r.result(self.s):
            self.winner=r.result(self.s);self.reason='checkmate';self._record('Charge ends in checkmate','end',[])
        else:self._terminal(1)
        return events

    def move(self,m):
        if m not in self.legal():raise ValueError('Illegal action')
        self._save()
        i,j,pro,tag=m;p=self.s.b[i];v=self.s.b[j]
        label=f'{self.white_move}{"." if self.side==0 else "..."} {"Saxons" if self.side==0 else "Normans"}: {r.symbol(i)} {"×" if v!="." else "→"} {r.symbol(j)}'
        if pro:label+=f'={pro.upper()}'
        if tag:label+=f' ({tag})'
        if self.phase=='bonus':label='BONUS KNIGHT: '+label
        r.apply(self.s,m)
        if self.phase=='response':
            self.bonus_left=2;self.phase='bonus';self.side=1
            self._record(label,'response',[i,j])
            if r.result(self.s):
                self.winner=r.result(self.s);self.reason='checkmate';self._record('Counterattack ends in checkmate','end',[])
            else:self._advance_bonus()
        elif self.phase=='bonus':
            self.bonus_left-=1;self._record(label,'bonus',[i,j])
            if r.result(self.s):
                self.winner=r.result(self.s);self.reason='checkmate';self._record('Knight strike ends in checkmate','end',[])
            else:self._advance_bonus()
        else:
            self._record(label,'ordinary',[i,j])
            if self.side==0:self.side=1
            else:self.side=0;self.white_move+=1
            self._terminal(self.side)
        return label

    def _advance_bonus(self):
        while self.bonus_left and not r.legal(self.s,1,True):
            self._record(f'Bonus knight action unavailable ({self.bonus_left} remaining).','bonus',[])
            self.bonus_left-=1
        if not self.bonus_left:
            self.phase='ordinary';self.side=0;self.white_move+=1
            self._terminal(0)

    def export(self):
        return dict(format='hastings-chess-1',seed=self.seed,hazard=self.hazard,
            events=self.log, winner=self.winner,reason=self.reason)


def replay_valid(data):
    if data.get('format')!='hastings-chess-1' or not isinstance(data.get('events'),list):
        raise ValueError('Not a Hastings Chess replay')
    for e in data['events']:
        if len(e['board'])!=64 or any(p not in '.PNBRQKHpnbrqkh' for p in e['board']):
            raise ValueError('Invalid replay board')
    return data
