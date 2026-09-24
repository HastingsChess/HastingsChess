"""Post-game only Hastings replay analysis. Never instantiate during live play."""
from dataclasses import dataclass
import math
import rules as r
from engine_uci import compatible
from hybrid import Hybrid,BENCHMARK_LEVEL_3

@dataclass(frozen=True)
class Score:
    cp_white:float=0
    mate_white:int|None=None
    note:str=''

def display(score):
    if score is None:return 'Analysing…'
    if score.mate_white is not None:
        return ('-' if score.mate_white<0 or score.mate_white==0 and score.cp_white<0 else '')+'M'+str(abs(score.mate_white))
    return f'{score.cp_white/100:+.2f}' if abs(score.cp_white)>=.5 else '0.00'

def white_fraction(score):
    if score is None:return .5
    if score.mate_white is not None:
        return .02 if score.mate_white<0 or score.mate_white==0 and score.cp_white<0 else .98
    return max(.02,min(.98,.5+.46*math.tanh(score.cp_white/450)))

class ReplayAnalyzer:
    def __init__(self,engine,nodes=1800):
        self.engine=engine;self.nodes=nodes
        self.hybrid=Hybrid(engine,level=BENCHMARK_LEVEL_3,nodes=nodes)

    def event(self,replay,index,cancel=None):
        if replay.get('format')!='hastings-chess-3':
            return None  # historical rule versions cannot be analysed as current Hastings
        e=replay['events'][index];s=r.state_from_dict(e)
        self.hybrid.cancel=cancel
        winner=e.get('result')
        if winner in ('white','black'):
            return Score(cp_white=100000 if winner=='white' else -100000,
                         mate_white=0,note='Game over: '+winner+' wins')
        if winner=='draw':return Score(note='Game over: draw')
        if e.get('next_phase')=='charge':
            return Score(r.evaluate(s,0)*100,note='Provisional position within the compulsory charge')
        side=int(e.get('side',0));move=int(e.get('move',1))
        mode=replay.get('bonus_mode','knight_pawn')
        if e.get('next_phase') in ('response','bonus','rescue_bonus'):
            value,_=self.hybrid._compound(s,move,normal=bool(e.get('normal_pending')),
                      left=int(e.get('bonus',0)),share=.2,preview=True,bonus_mode=mode)
            return Score(cp_white=-value,mate_white=-1 if value>=90000 else 1 if value<=-90000 else None,
                         note='Hastings compound Norman response')
        terminal=r.turn_terminal(s,side)
        if terminal=='draw':return Score(note='Stalemate')
        if terminal in ('white','black'):
            return Score(cp_white=100000 if terminal=='white' else -100000,
                         mate_white=0,note='Checkmate')
        if compatible(s,side):
            a=self.engine.analyse(s,side,move,nodes=self.nodes,cancel=cancel)[0]
            cp=a.cp if side==0 else -a.cp
            mate=(a.mate if side==0 else -a.mate) if a.mate is not None else None
        else:
            value=self.hybrid._leaf(s,side,move,.3)
            cp=value if side==0 else -value;mate=None
        note='Fairy-Stockfish and Hastings legality'
        if not e.get('charged'):
            # Conditional preview only. Never consult the game's future dice roll.
            upcoming=move if side==0 else move+1
            hazard={int(k):float(v) for k,v in replay.get('hazard',r.CHARGE_HAZARD).items()}
            chance=hazard.get(upcoming,0) if side==1 or e.get('attempted_move')!=move else 0
            if chance and mate is None:
                future=s.copy()
                if side==1:
                    best=self.engine.analyse(s,1,move,nodes=max(300,self.nodes//3),cancel=cancel)[0].move
                    r.apply(future,best)
                predicted=self.hybrid._charge_value(future,upcoming,0,.15,mode)
                if chance==1:
                    cp=predicted
                    mate=1 if predicted>=90000 else -1 if predicted<=-90000 else None
                else:cp=(1-chance)*cp+chance*max(-1200,min(1200,predicted))
                note=f'Fairy-Stockfish with {chance:.0%} conditional charge preview'
        return Score(cp_white=cp,mate_white=mate,note=note)
