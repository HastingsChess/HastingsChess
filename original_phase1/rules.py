"""Hastings Chess: random charge (conditional hazard on White turns 20-30).
 White H on a2/h2: moves 1/2 clear squares in any compass direction;
 captures king-like on adjacent square ONLY. H charges 2 forward, pawns 3,
 with push/capture obstruction rules. Normal promotions Q/R/B/N; charge
 promotions H. Black gets one ordinary action + two optional knight actions.
 Both bots use weak heuristic, not a chess engine. Reproducible random seeds.
 """
import random, math, collections, statistics, time

DIAG = [(1,1),(-1,1),(1,-1),(-1,-1)]
ORTH = [(0,1),(0,-1),(1,0),(-1,0)]
ALL = DIAG+ORTH
KNIGHT = [(1,2),(2,1),(-1,2),(-2,1),(1,-2),(2,-1),(-1,-2),(-2,-1)]
VAL = {'p':1,'h':4.5,'n':3.1,'b':3.35,'r':5.15,'q':9.3,'k':0}
FILE = 'abcdefgh'

def sq(x,y):return 8*y+x

def xy(i):return i%8,i//8

def onboard(x,y):return 0<=x<8 and 0<=y<8

def white(p):return p.isupper()

def enemy(p, q):return bool(q) and p.isupper()!=q.isupper()

def symbol(s):return FILE[s%8]+str(s//8+1)

class State:
 def __init__(self, hc=True):
  self.b = list('RNBQKBNR') + list('HPPPPPPH' if hc else 'PPPPPPPP')+['.']*32+list('pppppppp')+list('rnbqkbnr')
  # Castling, ep tracked manually
  self.castle={'K':True,'Q':True,'k':True,'q':True}
  self.ep=-1
  self.turn=0
  self.hm=0
  self.moves=[]
 def copy(self):
  z=State.__new__(State)
  z.b=self.b[:];z.castle=self.castle.copy();z.ep=self.ep;z.turn=self.turn;z.hm=self.hm
  z.moves=[]
  return z

def attacked(s,side,b):
 """Is square s attacked by side 0 white / 1 black?"""
 tx,ty=xy(s)
 p='P' if side==0 else 'p'
 py=ty-1 if side==0 else ty+1
 if 0<=py<8:
  for dx in (-1,1):
   x=tx+dx
   if 0<=x<8 and b[sq(x,py)]==p:return True
 n='N' if side==0 else 'n'
 for dx,dy in KNIGHT:
  x=tx+dx;y=ty+dy
  if onboard(x,y) and b[sq(x,y)]==n:return True
 k='K' if side==0 else 'k'
 h='H' if side==0 else 'h'
 q='Q' if side==0 else 'q'
 r='R' if side==0 else 'r'
 bishop='B' if side==0 else 'b'
 for dx,dy in ALL:
  x=tx+dx;y=ty+dy
  if onboard(x,y):
   a=b[sq(x,y)]
   if a in (k,h,q) or (a==r and (dx==0 or dy==0)) or (a==bishop and dx!=0 and dy!=0):return True
   if a!='.':continue
   xx=x+dx;yy=y+dy
   while onboard(xx,yy):
    a=b[sq(xx,yy)]
    if a!='.':
     if a==q or (a==r and (dx==0 or dy==0)) or (a==bishop and dx!=0 and dy!=0):return True
     break
    xx+=dx;yy+=dy
 return False

def in_check(s,side):
 key='K' if side==0 else 'k'
 try:i=s.b.index(key)
 except ValueError:return True
 return attacked(i,1-side,s.b)

def pseudo(s,side,knight_only=False):
 b=s.b; moves=[]
 def add(i,j,promo='',tag=''):
  if b[j]!='.' and b[j].lower()=='k':return
  moves.append((i,j,promo,tag))
 for i,p in enumerate(b):
  if p=='.' or int(p.islower())!=side:continue
  pt=p.lower();x,y=xy(i)
  if knight_only and pt!='n':continue
  if pt=='p':
   direction=1 if side==0 else -1
   ny=y+direction
   if 0<=ny<8:
    j=sq(x,ny)
    if b[j]=='.':
     if ny in (0,7):
      for promote in 'qrbn':add(i,j,promote)
     else:add(i,j)
     if y==(1 if side==0 else 6) and b[sq(x,y+2*direction)]=='.':add(i,sq(x,y+2*direction),'','double')
    for dx in (-1,1):
     xx=x+dx
     if 0<=xx<8:
      j=sq(xx,ny)
      if b[j]!='.' and enemy(p,b[j]):
       if ny in (0,7):
        for promote in 'qrbn':add(i,j,promote)
       else:add(i,j)
      elif j==s.ep:add(i,j,'','ep')
  elif pt=='n':
   for dx,dy in KNIGHT:
    xx=x+dx;yy=y+dy
    if onboard(xx,yy):
     j=sq(xx,yy)
     if b[j]=='.' or enemy(p,b[j]):add(i,j)
  elif pt=='k' or pt=='h':
   for dx,dy in ALL:
    xx=x+dx;yy=y+dy
    if onboard(xx,yy):
     j=sq(xx,yy)
     if b[j]=='.' or enemy(p,b[j]):add(i,j)
     # Only HOUSECARL: can MOVE a second square if BOTH squares are empty.
     # A second-square enemy piece can never be captured.
     if pt=='h' and b[j]=='.':
      xxx=xx+dx;yyy=yy+dy
      if onboard(xxx,yyy):
       jj=sq(xxx,yyy)
       if b[jj]=='.':add(i,jj)
   if pt=='k' and x==4 and y in (0,7):
    for cs,rook_x,empty,trans,to in ([('K' if side==0 else 'k'),7,[5,6],5,6], [('Q' if side==0 else 'q'),0,[1,2,3],3,2]):
     if s.castle[cs] and b[sq(rook_x,y)]==('R' if side==0 else 'r') and all(b[sq(x2,y)]=='.' for x2 in empty):
      if not in_check(s,side) and not attacked(sq(trans,y),1-side,b) and not attacked(sq(to,y),1-side,b):
       add(i,sq(to,y),'','castle')
  else:
   dirs=ALL if pt=='q' else DIAG if pt=='b' else ORTH
   for dx,dy in dirs:
    xx=x+dx;yy=y+dy
    while onboard(xx,yy):
     j=sq(xx,yy)
     if b[j]=='.':add(i,j)
     else:
      if enemy(p,b[j]):add(i,j)
      break
     xx+=dx;yy+=dy
 return moves

def apply(s,m,stats=None):
 i,j,pro,tag=m
 b=s.b; p=b[i];q=b[j]
 if stats is not None:
  if pro:stats['normal promotions']+=1;stats['normal promotion to '+pro.lower()]+=1
  if p=='H':stats['H moves']+=1
  if p=='H' and q!='.':stats['H captures']+=1;stats['H captures ' + q.lower()]+=1
  if q=='H':stats['H lost']+=1;stats['H killed by ' + p.lower()]+=1
 # capture rook on starting square prevents castling
 for square,cs in ((0,'Q'),(7,'K'),(56,'q'),(63,'k')):
  if i==square or j==square:s.castle[cs]=False
 if p=='K':s.castle['K']=s.castle['Q']=False
 if p=='k':s.castle['k']=s.castle['q']=False
 b[i]='.';b[j]=pro.upper() if p.isupper() and pro else pro.lower() if pro else p
 if tag=='ep':
  b[j+(-8 if p.isupper() else 8)]='.'
 if tag=='castle':
  rank=0 if p.isupper() else 7
  if j%8==6:rbeg,rend=7,5
  else:rbeg,rend=0,3
  b[sq(rend,rank)]=b[sq(rbeg,rank)];b[sq(rbeg,rank)]='.'
 s.ep=(i+j)//2 if tag=='double' else -1
 s.hm=0 if p.lower()=='p' or q!='.' else s.hm+1
 s.turn+=1

def legal(s,side,knight_only=False):
 ans=[]
 for m in pseudo(s,side,knight_only):
  t=s.copy();apply(t,m)
  if not in_check(t,side):ans.append(m)
 return ans

def evaluate(s,side,context=0):
 b=s.b; total=0
 for i,p in enumerate(b):
  if p=='.':continue
  t=p.lower();x,y=xy(i);home_y=y if p.isupper() else 7-y
  sig=1 if int(p.islower())==side else -1
  pos=0
  center=(3.5-abs(x-3.5))+(3.5-abs(y-3.5))
  if t=='p':pos=0.035*home_y + .025*(3.5-abs(x-3.5)) + .1*(home_y>=4)
  elif t=='n':pos=.075*center
  elif t=='b':pos=.03*center
  elif t=='h':pos=.06*center + .06*(home_y<=3)
  elif t=='k':pos=-.04*center if context<100 else .1*center
  elif t=='q':pos=.012*center
  total+=sig*(VAL[t]+pos)
 return total

# choose moves via material, positional, check and a crude next-capture exposure estimate

def _knight_hops(a,b):
    x,y=xy(a);tx,ty=xy(b)
    if (abs(x-tx),abs(y-ty)) in ((1,2),(2,1)):return 1
    for dx,dy in KNIGHT:
        xx,yy=x+dx,y+dy
        if onboard(xx,yy) and (abs(xx-tx),abs(yy-ty)) in ((1,2),(2,1)):
            return 2
    return 3

def _prep_score(t, side, phase, before):
    """Additional score for pre-charge planning, in pawn-equivalent units.
    Both sides know the importance of Norman cavalry; black also stages knights.
    Uses static threat checks and a deliberately modest positional preview,
    not an actual chess-engine search.
    """
    if phase<=7 or phase>=31:return 0.0
    progress=min(1,((phase-7)/22)**.85)
    knights=[i for i,p in enumerate(t.b) if p=='n']
    if side==0:
        # Black's knights are increasingly important targets to White.
        missing=before.b.count('n')-len(knights)
        score=missing*2.0*progress
        for i in knights:
            if attacked(i,0,t.b) and not attacked(i,0,before.b):
                score+=.34*progress
        return score
    score=0.0
    # Self-preservation: discourage every knight still on a capturable square,
    # not merely moves BY the knights; also reward guarding a knight.
    for i in knights:
        threat=attacked(i,0,t.b)
        defended=attacked(i,1,t.b)
        if threat:score-=(5.0 if not defended else 3.5)*progress
        elif defended:score+=.17*progress
        # Position for a post-charge counterattack instead of hiding knights.
        if phase>=19:
            targets=[(j,p) for j,p in enumerate(t.b) if p in 'QHRKP']
            # Predict a rough pawn landing square for move 30. Exact obstruction
            # effects are considered separately on Black's move 29.
            pawns=[sq(j%8,min(7,j//8+3)) for j,p in enumerate(t.b) if p=='P'] + [sq(j%8,min(7,j//8+2)) for j,p in enumerate(t.b) if p=='H']
            attack_potential=0.0
            for j,p in targets:
                dist=_knight_hops(i,j)
                if dist==1:attack_potential=max(attack_potential,{'Q':.36,'R':.25,'H':.25,'K':.25,'P':.04}[p])
                if dist==2 and p!='P':attack_potential=max(attack_potential,.11)
            if any(_knight_hops(i,j)==1 for j in pawns):attack_potential+=.08
            if not threat:score+=attack_potential*progress
    return score

def _move_score(s,t,m,side,phase,smart):
    i,j,pro,tag=m
    score=evaluate(t,side,context=s.turn)
    if attacked(j,1-side,t.b):
        score-=VAL[t.b[j].lower()]*(.46 if attacked(j,side,t.b) else .84)
    if in_check(t,1-side):score+=.28
    if tag=='castle':score+=.3
    if side==1 and phase<30 and s.b[i].lower()=='n' and attacked(j,0,t.b):score-=.7
    if side==0 and phase<30 and s.b[j].lower()=='n':score+=.3
    if smart:score+=_prep_score(t,side,phase,s)
    return score

def _best_knight_line(s, actions, branch=5):
    """Two-action lookahead for Norman knights; legal move generator checks pins.
    Return (best estimated score, best immediate action), as evaluated for Black.
    """
    if actions==0 or result(s) is not None:
        return evaluate(s,1),None
    opts=legal(s,1,knight_only=True)
    if not opts:return evaluate(s,1),None
    candidates=[]
    for m in opts:
        t=s.copy();apply(t,m)
        z=_move_score(s,t,m,1,30,False)
        candidates.append((z,m,t))
    candidates.sort(reverse=True,key=lambda x:x[0])
    # Examine a few good first moves plus a possible materially valuable fork.
    best=(-float('inf'),None)
    for score,m,t in candidates[:branch]:
        if result(t)=='black':z=1000
        elif actions>1:
            z,_=_best_knight_line(t,actions-1,branch=4)
        else:z=evaluate(t,1)
        # Mild tie-break towards a safer knight ending location.
        if t.b[m[1]]=='n' and attacked(m[1],0,t.b):z-=.6
        if z>best[0]:best=(z,m)
    return best

# Percent chance of charge, conditional on having reached the specified
# Saxon move WITHOUT a previous charge. The turn-30 charge is guaranteed.
CHARGE_HAZARD = {20:.01,21:.03,22:.05,23:.07,24:.09,25:.10,
                 26:.15,27:.25,28:.40,29:.60,30:1.0}

def choose(s, side, rng, phase=0, knight_only=False, strategic=True,
           bonus_remaining=0, charge_now=False):
    ms=legal(s,side,knight_only)
    if not ms:return None
    candidates=[]
    for m in ms:
        t=s.copy();apply(t,m)
        score=_move_score(s,t,m,side,phase,strategic)
        score+=rng.gauss(0,.18)
        candidates.append((score,m,t))
    candidates.sort(reverse=True,key=lambda x:x[0])
    # Preview the NEXT Saxon turn's possible charge. This intentionally uses
    # the actual position, without cheating by knowing the future RNG draw.
    # Exact multi-action tactical planning is reserved for the last few turns.
    next_hazard=CHARGE_HAZARD.get(phase+1,0)
    if strategic and side==1 and not knight_only and not charge_now and next_hazard>=.10:
        shortlist=candidates[:(7 if next_hazard>=.4 else 4)]
        ranked=[]
        for score,m,t in shortlist:
            f=t.copy();charge(f)
            charge_delta=evaluate(f,1)-evaluate(t,1)
            recovery,_=_best_knight_line(f,2,branch=3)
            recovery-=evaluate(f,1)
            ranked.append((score+next_hazard*(.30*charge_delta+.35*recovery),m,t))
        ranked.sort(key=lambda v:v[0],reverse=True)
        candidates=ranked+candidates[len(shortlist):]
        candidates.sort(key=lambda v:v[0],reverse=True)
    if strategic and side==1 and charge_now and not knight_only:
        # Black sees its ordinary action + TWO knight-only actions as one
        # sequence, using a shallow material-based knight-line search.
        ranked=[]
        for score,m,t in candidates[:10]:
            if in_check(t,0) and not legal(t,0):combined=1000
            else:combined,_=_best_knight_line(t,2,branch=5)
            ranked.append((.22*score+.78*combined,m,t))
        ranked.sort(key=lambda v:v[0],reverse=True)
        return ranked[0][1]
    if strategic and side==1 and charge_now and knight_only and bonus_remaining==2:
        ranked=[]
        for score,m,t in candidates[:8]:
            if in_check(t,0) and not legal(t,0):combined=1000
            else:combined,_=_best_knight_line(t,1,branch=5)
            ranked.append((.18*score+.82*combined,m,t))
        ranked.sort(key=lambda v:v[0],reverse=True)
        return ranked[0][1]
    if len(candidates)>2 and rng.random()<.21 and candidates[0][0]-candidates[1][0]<.65:
        return candidates[1][1]
    return candidates[0][1]

def charge(s,trace=None,turn=30):
    """Force all surviving White pawns 3 forwards and housecarls 2 forwards.
    Deterministic a-to-h, front-to-back ordering. A piece encountering a
    blocker pushes it one forward if vacant; otherwise captures an ENEMY
    blocker head-on. Friendly blockers that cannot be pushed remain in place.
    Neither king can be pushed or captured. King-check exposure permitted;
    a particular forced advance is skipped if it instantly checkmates White.
    Unique charge IDs follow pieces even if another unit pushes one ahead.
    Returns Counter of events and structured per-unit descriptions.
    """
    counts=collections.Counter(); events=[]
    ids=[i if p!='.' else None for i,p in enumerate(s.b)]
    order=sorted((i for i,p in enumerate(s.b) if p in ('P','H')),
                 key=lambda z:(z%8,-z//8))
    for uid in order:
        if uid not in ids:continue  # already captured during earlier part
        loc=ids.index(uid);unit=s.b[loc]
        if unit not in ('P','H'):continue
        cap=3 if unit=='P' else 2
        x,y=xy(loc); b=s.b[:]; piece_ids=ids[:]; target=loc
        cause='advance';blocker='.';pushed_from=None;pushed_to=None
        for yy in range(y+1,min(7,y+cap)+1):
            j=sq(x,yy); block=b[j]
            if block=='.':
                b[target]='.';piece_ids[target]=None
                b[j]=unit;piece_ids[j]=uid;target=j
                continue
            blocker=block
            if block.lower()=='k':cause='blocked by king';break
            beyond=sq(x,yy+1) if yy<7 else None
            if beyond is not None and b[beyond]=='.':
                b[beyond]=block;piece_ids[beyond]=piece_ids[j]
                b[target]='.';piece_ids[target]=None
                b[j]=unit;piece_ids[j]=uid;target=j
                cause='pushed';pushed_from=j;pushed_to=beyond
            elif enemy(unit,block):
                b[target]='.';piece_ids[target]=None
                b[j]=unit;piece_ids[j]=uid;target=j;cause='captured'
            else:cause='blocked by friend'
            break
        # A pushed pawn could itself arrive at rank eight: promote all
        # affected pawns on back rank as part of this compulsory charge.
        promoted=[]
        for j,p in enumerate(b):
            if p=='P' and j//8==7:
                b[j]='H';promoted.append(j)
        if target==loc and b==s.b:
            counts[cause]+=1
            events.append({'unit':unit,'from':symbol(loc),'to':symbol(loc),'event':cause,'blocker':blocker,'promoted':[]})
            if trace is not None:trace.append({'label':f'{turn}. {"Pawn" if unit=="P" else "Housecarl"} {symbol(loc)} stays ({cause})','phase':'charge','board':''.join(s.b),'squares':[loc],'description':f'Blocked by {blocker}.'})
            continue
        q=s.copy();q.b=b
        if in_check(q,0) and not legal(q,0):
            counts['checkmate exemption']+=1
            events.append({'unit':unit,'from':symbol(loc),'to':symbol(loc),'event':'checkmate exemption','blocker':blocker,'promoted':[]})
            if trace is not None:trace.append({'label':f'{turn}. {"Pawn" if unit=="P" else "Housecarl"} {symbol(loc)} stays (checkmate exemption)','phase':'charge','board':''.join(s.b),'squares':[loc],'description':'Forced movement would immediately leave the Saxon king checkmated; it is cancelled.'})
            continue
        s.b=b;ids=piece_ids
        # Forced displacement of a rook on its home square revokes castling.
        for home,right in ((0,'Q'),(7,'K'),(56,'q'),(63,'k')):
            if (s.b[home] != ('R' if right.isupper() else 'r')):
                s.castle[right]=False
        s.hm=0
        counts[cause]+=1
        counts['pawn promotions to H']+=len(promoted)
        if unit=='H':counts['housecarls charged']+=1
        else:counts['pawns charged']+=1
        event={'unit':unit,'from':symbol(loc),'to':symbol(target),'event':cause,'blocker':blocker,'promoted':[symbol(j) for j in promoted]}
        if pushed_from is not None:
            event['pushed_from']=symbol(pushed_from);event['pushed_to']=symbol(pushed_to)
        events.append(event)
        if trace is not None:
            unit_name='Pawn' if unit=='P' else 'Housecarl'
            details=f'{unit_name} {symbol(loc)} → {symbol(target)}.'
            marks=[loc,target]
            if cause=='pushed':details+=f' Pushes {blocker} from {symbol(pushed_from)} to {symbol(pushed_to)}.';marks.append(pushed_to)
            if cause=='captured':details+=f' Captures {blocker} head-on.'
            if promoted:details+=' Promotes '+', '.join(symbol(j) for j in promoted)+' to housecarl.'
            trace.append({'label':f'{turn}. Saxon {unit_name.lower()} charge: {symbol(loc)} → {symbol(target)} ({cause})','phase':'charge','board':''.join(s.b),'squares':marks,'description':details})
    s.ep=-1;s.turn+=1
    return counts,events

def turn_terminal(s,side):
    """Recognise checkmate or stalemate of the NEXT side about to act."""
    if legal(s,side):return None
    return ('black' if side==0 else 'white') if in_check(s,side) else 'draw'

def result(s):
    """Only immediate CHECKMATES, used within special multi-action turn."""
    for side in (0,1):
        if in_check(s,side) and not legal(s,side):return 'black' if side==0 else 'white'
    return None

def play(seed,hc=True,maxmoves=50,strategic=True,bonuses=2):
    rng=random.Random(seed);s=State(hc=hc)
    counts=collections.Counter();activity=collections.Counter()
    trace=[{'label':'Starting position: Saxon housecarls on a2 and h2',
      'phase':'opening','board':''.join(s.b),'squares':[8,15],
      'description':'Housecarls move one or two clear squares in any direction; capture only one adjacent square.'}]
    reached=False;charge_turn=None;charge_records=collections.Counter();charge_events=[]
    knights=0;housecarls=0;before=after=after_normal=after_counter=None
    bonus=0;bonus_victims=[];charge_before=charge_after=counter_after=None
    ended=None;end_kind=None;fullmove=0
    def do(m, side, move_num, phase='opening', label=None):
        i,j,pro,tag=m;p=s.b[i];victim=s.b[j]
        words={'p':'Pawn','h':'Housecarl','n':'Knight','b':'Bishop','r':'Rook','q':'Queen','k':'King'}
        desc=f'{words[p.lower()]} {symbol(i)} {"×" if victim!="." else "→"} {symbol(j)}'
        if pro:desc+=f' = {pro.upper()}'
        if tag=='ep':desc+=' (en passant)'
        if tag=='castle':desc='Castles '+('kingside' if j%8==6 else 'queenside')
        apply(s,m,activity)
        trace.append({'label':label or f'{move_num}{"." if side==0 else "..."} {"Saxons" if side==0 else "Normans"}: {desc}',
            'phase':phase,'board':''.join(s.b),'squares':[i,j], 'description':desc})
        return victim
    for move in range(1,maxmoves+1):
        fullmove=move
        ended=turn_terminal(s,0)
        if ended:break
        # Charge before White's ordinary action, if it triggers this round.
        if not reached and move in CHARGE_HAZARD and rng.random()<CHARGE_HAZARD[move]:
            reached=True;charge_turn=move;knights=s.b.count('n');housecarls=s.b.count('H')
            before=evaluate(s,0);charge_before=''.join(s.b)
            trace.append({'label':f'{move}. THE SAXON CHARGE!', 'phase':'charge',
              'board':''.join(s.b),'squares':[],
              'description':f'Random charge triggered on move {move}. All surviving Saxon pawns attempt three squares and housecarls two squares forwards, with push/capture rules. The Normans get one normal turn and two knight actions.'})
            charge_records,charge_events=charge(s,trace,turn=move)
            counts.update(charge_records);after=evaluate(s,0);charge_after=''.join(s.b)
            # If this unusual compulsory move left White checkmated (should
            # normally be stopped by each unit's exemption), terminate.
            ended=result(s)
            if ended:break
            # Black's normal turn, then exactly two KNIGHT-ONLY actions if legal.
            ended=turn_terminal(s,1)
            if ended:break
            m=choose(s,1,rng,phase=move,strategic=strategic,charge_now=True)
            if m is None:ended=turn_terminal(s,1) or 'draw';break
            do(m,1,move,phase='counter',label=f'{move}... Norman ordinary response: {symbol(m[0])} → {symbol(m[1])}')
            after_normal=evaluate(s,0)
            ended=result(s)
            if ended:break
            for k in range(bonuses):
                mm=choose(s,1,rng,phase=move,knight_only=True,strategic=strategic,bonus_remaining=bonuses-k,charge_now=True)
                if mm is None:
                    trace.append({'label':f'{move}... Norman bonus knight action {k+1}: unavailable','phase':'counter',
                      'board':''.join(s.b),'squares':[],'description':'No legal Norman knight move for this bonus action.'})
                    bonus_victims.append({'move':None,'victim':'.'})
                else:
                    i,j,_,_=mm;v=s.b[j];bonus_victims.append({'move':symbol(i)+symbol(j),'victim':v})
                    do(mm,1,move,phase='counter',label=f'{move}... Norman BONUS knight {k+1}: {symbol(i)} {"×" if v!="." else "→"} {symbol(j)}')
                    bonus+=1
                ended=result(s)
                if ended:break
            after_counter=evaluate(s,0);counter_after=''.join(s.b)
            if ended:break
            # Check Black's king and White's available moves as they resume.
            ended=turn_terminal(s,0)
            if ended:break
            continue
        # Ordinary round (White then Black). No further charges once triggered.
        m=choose(s,0,rng,phase=move,strategic=strategic)
        if m is None:ended=turn_terminal(s,0) or 'draw';break
        do(m,0,move,phase='opening' if not reached else 'aftermath')
        ended=turn_terminal(s,1)
        if ended:break
        m=choose(s,1,rng,phase=move,strategic=strategic)
        if m is None:ended=turn_terminal(s,1) or 'draw';break
        do(m,1,move,phase='opening' if not reached else 'aftermath')
        ended=turn_terminal(s,0)
        if ended:break
    if ended is None:
        end_kind='unfinished (move limit)'
    else:
        end_kind='stalemate' if ended=='draw' else 'checkmate'
    final_eval=evaluate(s,0)
    trace.append({'label':'End of recorded play' if ended else 'Move limit reached — unfinished',
      'phase':'end','board':''.join(s.b),'squares':[],
      'description':f'{end_kind}. '+('Saxons win.' if ended=='white' else 'Normans win.' if ended=='black' else 'Draw.' if ended=='draw' else 'No winner: unfinished game.')})
    return {'seed':seed,'reached':reached,'charge_turn':charge_turn,'before':before,'after':after,
      'norm_normal':after_normal,'after_norm':after_counter,'records':dict(counts),
      'events':charge_events,'knights':knights,'h_before':housecarls,'bonus':bonus,
      'bonus_victims':bonus_victims,'ended':ended,'outcome_type':end_kind,
      'played':fullmove,'remaining':dict(collections.Counter(s.b)),'board':''.join(s.b),
      'activity':dict(activity),'charge_before_board':charge_before,
      'charge_after_board':charge_after,'after_counter_board':counter_after,
      'trace':trace,'final_eval':final_eval}

if __name__=='__main__':
    import sys,json,time
    n=int(sys.argv[1]) if len(sys.argv)>1 else 10
    t=time.time()
    for i in range(n):
        g=play(i+123456)
        print(i+1,'charge turn',g['charge_turn'],'knights',g['knights'],g['ended'],g['outcome_type'],'time',round(time.time()-t,1),flush=True)
