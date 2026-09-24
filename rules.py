"""Hastings rules v2. Python is authoritative for all special actions."""
import random, math, collections, statistics, time

DIAG = [(1,1),(-1,1),(1,-1),(-1,-1)]
ORTH = [(0,1),(0,-1),(1,0),(-1,0)]
ALL = DIAG+ORTH
KNIGHT = [(1,2),(2,1),(-1,2),(-2,1),(1,-2),(2,-1),(-1,-2),(-2,-1)]
VAL = {'p':1,'h':3.2,'n':3.1,'b':3.35,'r':5.15,'q':9.3,'k':0}
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

def pseudo(s,side,knight_only=False,bonus_mode=None):
 if knight_only and bonus_mode is None:bonus_mode='knight_pawn'
 if bonus_mode not in (None,'knight_pawn'):raise ValueError('Unsupported pre-release experimental Norman bonus ruleset' if bonus_mode=='any_piece' else 'Unknown bonus ruleset')
 if bonus_mode and side!=1:raise ValueError('Only the Normans receive bonus actions')
 b=s.b; moves=[]
 def add(i,j,promo='',tag=''):
  if b[j]!='.' and b[j].lower()=='k':return
  moves.append((i,j,promo,tag))
 for i,p in enumerate(b):
  if p=='.' or int(p.islower())!=side:continue
  pt=p.lower();x,y=xy(i)
  if bonus_mode=='knight_pawn' and pt not in ('n','p'):continue
  if pt=='p':
   direction=1 if side==0 else -1
   ny=y+direction
   if 0<=ny<8:
    j=sq(x,ny)
    if bonus_mode=='knight_pawn':
     if ny!=0:
      if b[j]=='.' or (b[j]!='.' and enemy(p,b[j])):add(i,j,'','bonus_forward_capture' if b[j]!='.' else '')
      for dx in (-1,1):
       xx=x+dx
       if 0<=xx<8:
        jj=sq(xx,ny)
        if b[jj]!='.' and enemy(p,b[jj]):add(i,jj)
     continue
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
      elif b[j]=='.' and j==s.ep and b[j-direction*8]==('p' if side==0 else 'P'):add(i,j,'','ep')
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
   if pt=='k' and x==4 and y==(0 if side==0 else 7):
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

def legal(s,side,knight_only=False,bonus_mode=None):
 ans=[]
 for m in pseudo(s,side,knight_only,bonus_mode):
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

CHARGE_HAZARD={20:.01,21:.03,22:.05,23:.07,24:.09,25:.10,26:.15,27:.25,28:.40,29:.60,30:1.0}
RULESET='hastings-3-king-housecarl'

def state_dict(s):
    return dict(board=''.join(s.b),castle=s.castle.copy(),ep=s.ep,hm=s.hm,turn=s.turn)

def state_from_dict(d):
    s=State();s.b=list(d['board']);s.castle=d.get('castle',dict.fromkeys('KQkq',False)).copy()
    s.ep=d.get('ep',-1);s.hm=d.get('hm',0);s.turn=d.get('turn',0)
    return s

def charge(s, trace=None, turn=30):
    """Atomic per-unit advances; H capture range is measured from unit start.

    Kings never move. Skip a proposed completed unit action iff White is in
    check and has no ordinary legal reply in its resulting position. This test
    uses updated castling rights and expired EP. Check alone is permitted.
    """
    counts=collections.Counter();events=[]
    s.ep=-1  # the compulsory turn expires the preceding ordinary EP offer
    ids=[i if p!='.' else None for i,p in enumerate(s.b)]
    order=sorted((i for i,p in enumerate(s.b) if p in 'PH'),key=lambda i:(i%8,-i//8))
    irreversible=False
    def record(event, marks):
        events.append(event);counts[event['event']]+=1
        if trace is not None:
            name='Housecarl' if event['unit']=='H' else 'Pawn'
            label=f"{turn}. {name} charge: {event['from']} → {event['to']} ({event['event']})"
            trace.append(dict(label=label,phase='charge',squares=marks,description=label,
                              event=event.copy(),**state_dict(s)))
    for uid in order:
        if uid not in ids:continue
        loc=ids.index(uid);unit=s.b[loc]
        if unit not in 'PH':continue
        x,y=xy(loc);q=s.copy();b=q.b;newids=ids[:];target=loc
        cap=3 if unit=='P' else 2
        cause='advance';blocker='.';pushed=None;captured=None
        for yy in range(y+1,min(7,y+cap)+1):
            j=sq(x,yy);blocker=b[j]
            if blocker=='.':
                b[target]='.';newids[target]=None;b[j]=unit;newids[j]=uid;target=j
                continue
            if blocker.lower()=='k':cause='blocked by king';break
            beyond=j+8 if yy<7 else None
            if beyond is not None and b[beyond]=='.':
                b[beyond]=blocker;newids[beyond]=newids[j]
                b[target]='.';newids[target]=None;b[j]=unit;newids[j]=uid;target=j
                cause='pushed';pushed=dict(piece=blocker,from_square=j,to_square=beyond)
            elif enemy(unit,blocker) and (unit=='P' or yy-y==1):
                captured=blocker;b[target]='.';newids[target]=None
                b[j]=unit;newids[j]=uid;target=j;cause='captured'
            elif enemy(unit,blocker):cause='blocked by housecarl capture range'
            else:cause='blocked by friend'
            break
        promoted=[]
        for j,p in enumerate(b):
            if p=='P' and j//8==7:b[j]='H';promoted.append(j)
        # Rook identity, not just presence of another rook, controls rights.
        for home,right in ((0,'Q'),(7,'K'),(56,'q'),(63,'k')):
            if ids[home]!=newids[home]:q.castle[right]=False
        event=dict(unit=unit,from_square=loc,to_square=target,
                   **{'from':symbol(loc),'to':symbol(target),'event':cause},
                   blocker=blocker,promoted=[symbol(j) for j in promoted])
        if pushed:event['push']=pushed
        if captured:event['captured']=captured
        if q.b!=s.b and in_check(q,0) and not legal(q,0):
            event.update(to=symbol(loc),to_square=loc,event='checkmate exemption',promoted=[])
            event.pop('push',None);event.pop('captured',None)
            record(event,[loc]);continue
        changed=q.b!=s.b
        if changed:
            irreversible |= unit=='P' or captured is not None or (pushed is not None and pushed['piece'].lower()=='p')
            s.b=q.b;s.castle=q.castle;ids=newids
            counts['pawn promotions to H']+=len(promoted)
            counts['housecarls charged' if unit=='H' else 'pawns charged']+=1
        record(event,list(dict.fromkeys([loc,target]+([pushed['to_square']] if pushed else []))))
    s.hm=0 if irreversible else s.hm+1;s.turn+=1
    return counts,events

def turn_terminal(s,side):
    if legal(s,side):return None
    return ('black' if side==0 else 'white') if in_check(s,side) else 'draw'

def result(s):
    for side in (0,1):
        if in_check(s,side) and not legal(s,side):return 'black' if side==0 else 'white'
    return None
