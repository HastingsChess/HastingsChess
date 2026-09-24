"""Bounded custom alpha-beta search. No Stockfish strength is claimed."""
import math
import random
import time
import rules as r

class Search:
    def __init__(self, level=2, seconds=1.0):
        self.level=level;self.seconds=seconds;self.nodes=0;self.cache={};self.cancel=None;self.precharge=True

    def score(self,s,side,phase=0):
        v=r.evaluate(s,side,phase)
        # Knights matter more as the guaranteed counterattack approaches.
        k=s.b.count('n')
        if self.precharge and 15<=phase<=30:
            v+=(1 if side==1 else -1)*.45*k*((phase-14)/16)
        for i,p in enumerate(s.b):
            if p=='H':
                mobility=sum(1 for m in r.pseudo(s,0) if m[0]==i)
                v+=(1 if side==0 else -1)*min(mobility,12)*.025
            if p=='n' and self.precharge and 18<=phase<=30 and r.attacked(i,0,s.b):
                v+=(1 if side==0 else -1)*.3
        return v

    def _moves(self,s,side,bonus=False):
        moves=r.legal(s,side,bonus_mode=self.bonus_mode if bonus else None)
        def order(m):
            i,j,pro,_=m
            victim=s.b[j]
            return (10*r.VAL[victim.lower()]-r.VAL[s.b[i].lower()] if victim!='.' else 0)+(8 if pro else 0)
        moves.sort(key=order,reverse=True)
        return moves

    def _ab(self,s,side,depth,alpha,beta,root,deadline,phase):
        self.nodes+=1
        if time.monotonic()>deadline or (self.cancel and self.cancel.is_set()):raise TimeoutError
        key=(''.join(s.b),tuple(s.castle.values()),s.ep,s.hm,side,depth,root,phase,self.precharge)
        if key in self.cache:
            value,flag=self.cache[key]
            if flag=='exact':return value
            if flag=='lower':alpha=max(alpha,value)
            else:beta=min(beta,value)
            if alpha>=beta:return value
        original_alpha,original_beta=alpha,beta
        ms=self._moves(s,side)
        if not ms:
            if r.in_check(s,side):return (-10000-depth if side==root else 10000+depth)
            return 0
        if depth<=0:
            return self._quiet(s,side,alpha,beta,root,deadline,phase,3)
        maximizing=side==root
        best=-math.inf if maximizing else math.inf
        for m in ms:
            t=s.copy();r.apply(t,m)
            v=self._ab(t,1-side,depth-1,alpha,beta,root,deadline,phase)
            if maximizing:best=max(best,v);alpha=max(alpha,best)
            else:best=min(best,v);beta=min(beta,best)
            if beta<=alpha:break
        if len(self.cache)<25000:
            flag='upper' if best<=original_alpha else 'lower' if best>=original_beta else 'exact'
            self.cache[key]=(best,flag)
        return best

    def choose(self,g,cancel=None):
        self.cache.clear();self.nodes=0;self.cancel=cancel;self.precharge=not g.charged;self.bonus_mode=g.bonus_mode
        ms=g.legal()
        if not ms:return None
        deadline=time.monotonic()+max(.05,self.seconds)
        root=g.side; best=ms[0]
        ms=self._moves(g.s,root,g.phase in ('bonus','rescue_bonus'))
        # Iterative deepening; keep the last completed iteration.
        for depth in range(1,max(1,self.level)+1):
            try:
                choices=[]
                for m in ms:
                    t=g.s.copy();r.apply(t,m)
                    if g.phase=='response':
                        v=self._counter(t,2,deadline,g.white_move)
                    elif g.phase in ('bonus','rescue_bonus'):
                        v=self._counter(t,g.bonus_left-1,deadline,g.white_move,
                                        normal=g.normal_pending)
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

    def _quiet(self,s,side,alpha,beta,root,deadline,phase,left):
        if time.monotonic()>deadline or (self.cancel and self.cancel.is_set()):raise TimeoutError
        check=r.in_check(s,side);moves=self._moves(s,side)
        if not moves:return (-10000 if side==root else 10000) if check else 0
        stand=self.score(s,root,phase)
        if not left:return stand
        maximizing=side==root
        best=(-math.inf if maximizing else math.inf) if check else stand
        if not check:
            if maximizing:alpha=max(alpha,best)
            else:beta=min(beta,best)
            if alpha>=beta:return best
            moves=[m for m in moves if s.b[m[1]]!='.' or m[2] or m[3]=='ep']
        for m in moves:
            t=s.copy();r.apply(t,m)
            v=self._quiet(t,1-side,alpha,beta,root,deadline,phase,left-1)
            if maximizing:best=max(best,v);alpha=max(alpha,best)
            else:best=min(best,v);beta=min(beta,best)
            if alpha>=beta:break
        return best

    def _counter(self,s,left,deadline,phase,normal=False):
        if time.monotonic()>deadline or (self.cancel and self.cancel.is_set()):raise TimeoutError
        if r.result(s)=='black':return 10000
        if normal:
            ordinary=self._moves(s,1)
            if ordinary:
                return max(self._counter(self._after(s,m),left,deadline,phase) for m in ordinary[:24])
            if not left:return -10000 if r.in_check(s,1) else 0
        if not left:return self.score(s,1,phase)
        ms=self._moves(s,1,True)
        if not ms:return self.score(s,1,phase)
        best=-math.inf
        for m in ms[:24]:
            t=self._after(s,m)
            best=max(best,self._counter(t,left-1,deadline,phase,normal=normal))
        return best

    @staticmethod
    def _after(s,m):
        t=s.copy();r.apply(t,m);return t
