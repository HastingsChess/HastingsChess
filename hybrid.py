"""Fairy-Stockfish ordinary search plus bounded Hastings chance/compound branches.

Engine CP values decide ordinary play. Python generates true special actions,
then the real engine searches the resulting ordinary White-to-move positions.
Chance planning samples the next White turn and never reads the game's RNG.
"""
import time,math
import rules as r
from engine_uci import FairyEngine,EngineError,SearchCancelled,compatible,uci_move

LEVELS={1:(.16,2,400),2:(.6,4,2500),3:(1.6,5,10000),
        4:(2.2,6,16000),5:(3.0,7,24000),6:(4.0,8,40000),
        7:(5.2,9,65000),8:(6.8,10,95000),9:(9.0,12,140000),10:(12.0,14,200000)}
LEVEL_NAMES=('Beginner','Casual','Club','Intermediate','Strong Club',
             'Advanced','Expert','Very Strong','Master','Maximum')

class Hybrid:
    def __init__(self,engine=None,level=3,seconds=None,nodes=None):
        if int(level) not in LEVELS:raise ValueError('Difficulty must be 1–10')
        self.engine=engine or FairyEngine();self.level=int(level)
        default,self.candidates,self.base_nodes=LEVELS[self.level]
        self.seconds=seconds if seconds is not None else default
        self.fixed_nodes=nodes;self.last_info={};self.cancel=None

    def _check(self):
        if self.cancel and self.cancel.is_set():raise SearchCancelled('Search cancelled')

    def _analyse(self,s,side,move=1,multipv=1,share=1.0):
        self._check()
        nodes=max(150,int(self.fixed_nodes*share)) if self.fixed_nodes is not None else None
        return self.engine.analyse(s,side,move,multipv=multipv,
                movetime=max(15,int(self.seconds*1000*share)),nodes=nodes,cancel=self.cancel)

    def _cavalry(self,s,white_move):
        """Modest extra CP reserve for pre-charge cavalry, beyond ordinary material."""
        progress=min(1,max(0,white_move)/30)
        reserve=35+95*progress*progress
        score=0
        for i,p in enumerate(s.b):
            if p!='n':continue
            score+=reserve
            mobility=sum(1 for m in r.pseudo(s,1,True) if m[0]==i)
            score+=min(mobility,6)*2*progress
            if r.attacked(i,0,s.b):score-=18*progress
        return score

    def _cheap(self,s):
        # Used only to order/prune compound paths before real engine evaluation.
        score=r.evaluate(s,1)*100
        for i,p in enumerate(s.b):
            if p!='.' and p.islower() and p!='k' and r.attacked(i,0,s.b):
                score-=r.VAL[p]*40*(.5 if r.attacked(i,1,s.b) else 1)
        if r.in_check(s,0):score+=25
        return score

    def _terminal_cp(self,s,side):
        ms=r.legal(s,side)
        if not ms:return (-100000 if r.in_check(s,side) else 0)
        return None

    def _leaf(self,s,side,move,share):
        terminal=self._terminal_cp(s,side)
        if terminal is not None:return terminal
        if s.hm>=100:return 0
        if compatible(s,side):return self._analyse(s,side,move,share=share)[0].cp
        # Explicit bridge for non-moving king check: search actual legal actions
        # in Python until an ordinary representable position is reached.
        options=[]
        for m in r.legal(s,side):
            t=s.copy();r.apply(t,m)
            options.append((r.evaluate(t,side),m,t))
        options.sort(key=lambda x:x[0],reverse=True)
        values=[]
        for _,m,t in options[:self.candidates]:
            self._check()
            if compatible(t,1-side):values.append(-self._leaf(t,1-side,move+(side==1),share/max(1,self.candidates)))
        if not values:raise EngineError('Special position cannot be bridged safely to Fairy-Stockfish; select the lightweight opponent.')
        return max(values)

    def _compound(self,s,white_move,normal=True,left=2,share=1.0,preview=False,bonus_mode='knight_pawn'):
        """Beam over the whole Black sequence; terminal mates stop immediately.

        Each node carries its complete action path. Endpoint scores include a
        real White reply search, so winning material while hanging a queen is
        not judged from static material alone. Beam width is explicitly bounded.
        """
        self._check();width=(10 if preview else 16)+self.level*3
        nodes=[(s,[],self._cheap(s),normal,left)]
        finalists=[]
        for stage in range(left+int(normal)):
            seen={}
            for board,path,_,pending,remaining in nodes:
                self._check()
                if not pending and not remaining:
                    finalists.append((board,path));continue
                ordinary=r.legal(board,1) if pending else []
                rescue=pending and not ordinary and r.in_check(board,1)
                moves=ordinary if pending and ordinary else r.legal(board,1,bonus_mode=bonus_mode) if remaining and (rescue or not pending) else []
                if not moves:
                    if pending:
                        # No ordinary response or rescue: a genuine terminal state.
                        if not path:return (-100000 if r.in_check(board,1) else 0),path
                        finalists.append((board,path));continue
                    finalists.append((board,path));continue
                for m in moves:
                    t=board.copy();r.apply(t,m)
                    if r.in_check(t,0) and not r.legal(t,0):return 100000,path+[m]
                    npending=pending if rescue else False
                    nleft=remaining-1 if rescue or not pending else remaining
                    key=(''.join(t.b),tuple(t.castle.values()),t.ep,npending,nleft)
                    value=self._cheap(t)
                    if key not in seen:seen[key]=(t,path+[m],value,npending,nleft)
            nodes=sorted(seen.values(),key=lambda n:n[2],reverse=True)[:width]
            if not nodes:break
        finalists.extend((b,p) for b,p,_,_,_ in nodes)
        finalists=finalists[:(2+self.level//2 if preview else 4+self.level)]
        ranked=[]
        for board,path in finalists:
            if not path:continue
            value=-self._leaf(board,0,white_move+1,share/max(1,len(finalists)))
            ranked.append((value,path))
        if not ranked and not normal:
            return -self._leaf(s,0,white_move+1,share),[]
        if not ranked:raise EngineError('No legal counterattack continuation')
        return max(ranked,key=lambda x:x[0])

    def _charge_value(self,s,move,root,share,bonus_mode):
        # A mate/stalemate before the new White turn takes precedence.
        term=self._terminal_cp(s,0)
        if term is not None:return term if root==0 else -term
        c=s.copy();r.charge(c)
        if r.in_check(c,0) and not r.legal(c,0):return -100000 if root==0 else 100000
        black,path=self._compound(c,move,normal=True,left=2,share=share,preview=True,bonus_mode=bonus_mode)
        return black if root==1 else -black

    def choose(self,g,cancel=None):
        start=time.monotonic();calls=self.engine.calls;nodes=self.engine.total_nodes
        self.cancel=cancel;self._check();legal=g.legal()
        if not legal:return None
        if g.phase in ('response','bonus','rescue_bonus'):
            value,path=self._compound(g.s,g.white_move,normal=g.normal_pending,
                left=g.bonus_left,share=.85,bonus_mode=g.bonus_mode)
            move=next((m for m in path if m is not None),None)
            if move not in legal:raise EngineError('Compound search returned an invalid first action')
            detail='Complete Norman sequence with Fairy-Stockfish endpoint search'
        elif not compatible(g.s,g.side):
            ranked=[]
            for m in legal:
                t=g.s.copy();r.apply(t,m)
                ranked.append((-self._leaf(t,1-g.side,g.white_move,.8/len(legal)),m))
            value,move=max(ranked,key=lambda x:x[0]);detail='Python legality bridge + Fairy-Stockfish'
        else:
            chance=g.hazard.get(g.white_move+1,0) if not g.charged else 0
            analysis=self._analyse(g.s,g.side,g.white_move,multipv=self.candidates,
                                   share=.58 if chance else .92)
            ranked=[]
            for a in analysis:
                self._check();t=g.s.copy();r.apply(t,a.move);value=float(a.cp)
                if not g.charged:
                    adjustment=self._cavalry(t,g.white_move)-self._cavalry(g.s,g.white_move)
                    value+=adjustment if g.side==1 else -adjustment
                # Never replace a proved mate with a speculative preview.
                if chance and a.mate is None and abs(value)<20000:
                    future=t
                    if g.side==0:
                        replies={uci_move(m):m for m in r.legal(t,1)}
                        reply=replies.get(a.pv[1]) if len(a.pv)>1 else None
                        if reply is None and replies:
                            reply=self._analyse(t,1,g.white_move,share=.03)[0].move
                        if reply is not None:future=t.copy();r.apply(future,reply)
                    charge_cp=self._charge_value(future,g.white_move+1,g.side,.35/len(analysis),g.bonus_mode)
                    value=(1-chance)*value+chance*charge_cp
                ranked.append((value,a.move))
            value,move=max(ranked,key=lambda x:x[0]);detail=f'Fairy-Stockfish MultiPV + Hastings planning (next charge {chance:.0%})'
        if move not in legal:raise EngineError('Search returned an illegal Hastings move')
        self.last_info=dict(engine=self.engine.name,mode='Fairy-Stockfish hybrid',
            calls=self.engine.calls-calls,nodes=self.engine.total_nodes-nodes,
            seconds=time.monotonic()-start,score_cp=value,detail=detail)
        return move

    def close(self):self.engine.close()
