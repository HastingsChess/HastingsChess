"""Bounded custom alpha-beta search. No Stockfish strength is claimed."""
import math
import random
import time
import rules as r

class Search:
    def __init__(self, level=2, seconds=1.0):
        self.level=level;self.seconds=seconds;self.nodes=0;self.cache={}

    def score(self,s,side,phase=0):
        v=r.evaluate(s,side,phase)
        # Knights matter more as the guaranteed counterattack approaches.
        k=s.b.count('n')
        if 15<=phase<=30:
            v+=(1 if side==1 else -1)*.45*k*((phase-14)/16)
        for i,p in enumerate(s.b):
            if p=='H':
                mobility=sum(1 for m in r.pseudo(s,0) if m[0]==i)
                v+=(1 if side==0 else -1)*min(mobility,12)*.025
            if p=='n' and 18<=phase<=30 and r.attacked(i,0,s.b):
                v+=(1 if side==0 else -1)*.3
        return v

    def _moves(self,s,side,knights=False):
        moves=r.legal(s,side,knights)
        def order(m):
            i,j,pro,_=m
            victim=s.b[j]
            return (10*r.VAL[victim.lower()]-r.VAL[s.b[i].lower()] if victim!='.' else 0)+(8 if pro else 0)
        moves.sort(key=order,reverse=True)
        return moves

    def _ab(self,s,side,depth,alpha,beta,root,deadline,phase):
        self.nodes+=1
        if time.monotonic()>deadline:raise TimeoutError
        key=(''.join(s.b),tuple(s.castle.values()),s.ep,side,depth)
        if key in self.cache:return self.cache[key]
        ms=self._moves(s,side)
        if not ms:
            if r.in_check(s,side):return (-10000-depth if side==root else 10000+depth)
            return 0
        if depth<=0:
            # One-ply forcing capture/check extension at leaves, bounded.
            return self.score(s,root,phase)
        maximizing=side==root
        best=-math.inf if maximizing else math.inf
        for m in ms:
            t=s.copy();r.apply(t,m)
            v=self._ab(t,1-side,depth-1,alpha,beta,root,deadline,phase)
            if maximizing:best=max(best,v);alpha=max(alpha,best)
            else:best=min(best,v);beta=min(beta,best)
            if beta<=alpha:break
        if len(self.cache)<25000:self.cache[key]=best
        return best

    def choose(self,g):
        ms=g.legal()
        if not ms:return None
        deadline=time.monotonic()+max(.05,self.seconds)
        root=g.side; best=ms[0]
        ms=self._moves(g.s,root,g.phase=='bonus')
        # Iterative deepening; keep the last completed iteration.
        for depth in range(1,max(1,self.level)+1):
            try:
                choices=[]
                for m in ms:
                    t=g.s.copy();r.apply(t,m)
                    if g.phase=='response':
                        v=self._counter(t,2,deadline,g.white_move)
                    elif g.phase=='bonus':
                        v=self._counter(t,g.bonus_left-1,deadline,g.white_move)
                    else:
                        v=self._ab(t,1-root,depth-1,-math.inf,math.inf,root,deadline,g.white_move)
                        if root==1 and not g.charged and g.hazard.get(g.white_move+1,0):
                            # Conditional next-turn chance, not a peek at the RNG.
                            c=t.copy();r.charge(c)
                            chance=g.hazard[g.white_move+1]
                            v+=chance*.40*(self.score(c,1,g.white_move+1)-self.score(t,1,g.white_move+1))
                    choices.append((v,m))
                if choices:
                    choices.sort(key=lambda x:x[0],reverse=True)
                    best=choices[0][1]
                    ms=[m for _,m in choices]
            except TimeoutError:break
        return best

    def _counter(self,s,left,deadline,phase):
        if time.monotonic()>deadline:raise TimeoutError
        if r.result(s)=='black':return 10000
        if not left:return self.score(s,1,phase)
        ms=self._moves(s,1,True)
        if not ms:return self.score(s,1,phase)
        best=-math.inf
        for m in ms[:24]:
            t=s.copy();r.apply(t,m)
            best=max(best,self._counter(t,left-1,deadline,phase))
        return best
