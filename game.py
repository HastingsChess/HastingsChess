"""Authoritative Hastings turns; v2 snapshots describe state AFTER events."""
import copy,random
import rules as r

class Game:
    def __init__(self,seed=1,hazard=None,bonus_mode='knight_pawn'):
        if bonus_mode not in ('knight_pawn','any_piece'):raise ValueError('Unknown Norman bonus ruleset')
        self.bonus_mode=bonus_mode
        self.seed=int(seed);self.rng=random.Random(self.seed)
        self.hazard=dict(r.CHARGE_HAZARD if hazard is None else hazard)
        if any(not isinstance(k,int) or k<1 or not 0<=v<=1 for k,v in self.hazard.items()):
            raise ValueError('Hazards must map positive White move numbers to probabilities 0–1')
        self.s=r.State();self.side=0;self.white_move=1;self.charged=False
        self.phase='ordinary';self.bonus_left=0;self.normal_pending=False;self.attempted_move=None
        self.winner=None;self.reason='';self.history=[];self.log=[]
        self._record('The Saxons assemble. Nothing could possibly go wrong.','start',[])

    def clone(self):
        g=copy.copy(self);g.s=self.s.copy();g.rng=random.Random();g.rng.setstate(self.rng.getstate())
        g.hazard=self.hazard.copy();g.log=self.log[:];g.history=[]
        return g

    def _snapshot(self):
        return dict(**r.state_dict(self.s),side=self.side,move=self.white_move,
                    bonus=self.bonus_left,normal_pending=self.normal_pending,bonus_mode=self.bonus_mode,
                    charged=self.charged,next_phase=self.phase,
                    attempted_move=self.attempted_move,result=self.winner,reason=self.reason)

    def _record(self,label,phase,squares,**extra):
        self.log.append(dict(label=label,phase=phase,squares=squares,**self._snapshot(),**extra))

    def _save(self):
        self.history.append((self.s.copy(),self.side,self.white_move,self.charged,
            self.phase,self.bonus_left,self.normal_pending,self.winner,self.reason,self.attempted_move,
            self.rng.getstate(),len(self.log)))

    def undo(self):
        if not self.history:return False
        (self.s,self.side,self.white_move,self.charged,self.phase,self.bonus_left,
         self.normal_pending,self.winner,self.reason,self.attempted_move,rs,n)=self.history.pop()
        self.rng.setstate(rs);self.log=self.log[:n];return True

    def odds(self):
        move=self.white_move+(self.side==1)
        return self.hazard.get(move,0) if not self.charged else 0

    def legal(self):
        return [] if self.winner else r.legal(self.s,self.side,
            bonus_mode=self.bonus_mode if self.phase in ('bonus','rescue_bonus') else None)

    def _end(self,winner,reason):
        self.winner=winner;self.reason=reason
        self._record(f'Game over: {reason} ({winner})','end',[])

    def _terminal(self,side):
        z=r.turn_terminal(self.s,side)
        if z:self._end(z,'stalemate' if z=='draw' else 'checkmate')
        elif self.s.hm>=100:self._end('draw','fifty-move rule')

    def start_turn(self):
        if self.winner or self.side!=0 or self.charged or self.attempted_move==self.white_move:return
        self._terminal(0)
        if self.winner:return
        chance=self.hazard.get(self.white_move,0)
        if not chance:self.attempted_move=self.white_move;return
        self._save();self.attempted_move=self.white_move
        draw=self.rng.random()
        if draw>=chance:
            self._record(f'{self.white_move}. Charge avoided ({chance:.0%} chance).','hazard',[],draw=draw,probability=chance)
            return
        self.charged=True;self.phase='charge'
        self._record(f'{self.white_move}. THE SAXON CHARGE! The dice hate somebody.','charge',[],draw=draw,probability=chance)
        trace=[];_,events=r.charge(self.s,trace,turn=self.white_move)
        for t in trace:
            entry=self._snapshot();entry.update(t);self.log.append(entry)
        self.phase='response';self.side=1;self.bonus_left=2;self.normal_pending=True
        self._record('Charge complete. Norman response and two bonus actions remain.','charge_end',[])
        self._prepare_response()
        return events

    def move(self,m):
        expected_side=self.side
        if self.side==0:self.start_turn()
        if self.side!=expected_side or self.winner:raise ValueError('Turn changed before this move: process the charge first')
        m=tuple(m)
        if m not in self.legal():raise ValueError('Illegal action')
        self._save();i,j,pro,tag=m;p=self.s.b[i];v=self.s.b[j]
        side=self.side;phase=self.phase;number=self.white_move
        if tag=='ep':v='p' if side==0 else 'P'
        label=f'{number}{"." if side==0 else "..."} {"Saxons" if side==0 else "Normans"}: {r.symbol(i)} {"×" if v!="." else "→"} {r.symbol(j)}'
        if pro:label+=f'={pro.upper()}'
        if tag:label+=f' ({tag})'
        if phase in ('bonus','rescue_bonus'):
            label=f'BONUS {"KNIGHT" if p.lower()=="n" else "PAWN" if p.lower()=="p" else "PIECE"} {3-self.bonus_left}: '+label
        r.apply(self.s,m)
        if phase=='response':self.normal_pending=False;self.phase='bonus'
        elif phase in ('bonus','rescue_bonus'):self.bonus_left-=1
        elif side==0:self.side=1
        else:self.side=0;self.white_move+=1
        self._record(label,phase,[i,j],action=list(m),actor=side,action_move=number,piece=p,captured=v)
        if phase in ('response','bonus','rescue_bonus'):
            if r.in_check(self.s,0) and not r.legal(self.s,0):self._end('black','checkmate')
            else:self._advance_counter()
        else:self._terminal(self.side)
        return label

    def _prepare_response(self):
        if r.legal(self.s,1):self.phase='response';return
        if r.in_check(self.s,1) and self.bonus_left and r.legal(self.s,1,bonus_mode=self.bonus_mode):
            self.phase='rescue_bonus'
            self._record('The Norman king is in check: a legal bonus action must rescue it before the ordinary response.','rescue_notice',[])
            return
        self._terminal(1)

    def _advance_counter(self):
        if self.normal_pending:
            self._prepare_response();return
        while self.bonus_left and not r.legal(self.s,1,bonus_mode=self.bonus_mode):
            number=3-self.bonus_left;self.bonus_left-=1
            self._record(f'Bonus action {number}: none available.','bonus',[],skipped=True)
        if self.bonus_left:self.phase='bonus';return
        self.phase='ordinary';self.side=0;self.white_move+=1
        self._record('The counterattack has finished. Ordinary chess resumes.','counter_end',[])
        self._terminal(0)

    def export(self):
        return dict(format='hastings-chess-3',ruleset=r.RULESET+'-'+self.bonus_mode,
                    bonus_mode=self.bonus_mode,seed=self.seed,hazard=self.hazard,
                    events=copy.deepcopy(self.log),winner=self.winner,reason=self.reason)


def replay_valid(data):
    if not isinstance(data,dict) or data.get('format') not in ('hastings-chess-1','hastings-chess-2','hastings-chess-3'):
        raise ValueError('Not a Hastings Chess replay')
    events=data.get('events')
    if not isinstance(events,list) or not events or len(events)>100000:raise ValueError('Replay needs 1–100000 events')
    for e in events:
        if not isinstance(e,dict) or not isinstance(e.get('board'),str):raise ValueError('Missing replay board')
        b=e['board']
        if len(b)!=64 or any(p not in '.PNBRQKHpnbrqkh' for p in b) or b.count('K')!=1 or b.count('k')!=1:
            raise ValueError('Invalid replay board or king count')
        if not isinstance(e.get('label'),str) or not isinstance(e.get('phase'),str):raise ValueError('Missing event label/phase')
        if any(not isinstance(i,int) or not 0<=i<64 for i in e.get('squares',[])):raise ValueError('Invalid highlighted square')
    return data
