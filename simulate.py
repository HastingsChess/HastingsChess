"""Seeded benchmarks. Every row names the actual opponent and its engine calls."""
import argparse,importlib.util,json,statistics,time,threading
from collections import Counter
from pathlib import Path
import rules as r
from game import Game
from ai import Search
from hybrid import Hybrid,BENCHMARK_LEVEL_3,LEVELS
from engine_uci import FairyEngine,SearchCancelled

BASE=Path(__file__).resolve().parent

class Opponent:
 def __init__(self,kind,level,seconds,nodes=None):
  self.kind=kind;self.level=level;self.seconds=seconds;self.engine=None;self.nodes=nodes
  if kind=='fairy':self.engine=FairyEngine()
  if kind=='legacy':
   spec=importlib.util.spec_from_file_location('hastings_legacy_ai',BASE/'original_phase1/ai.py')
   self.legacy=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.legacy)
 def choose(self,g,cancel=None):
  begin=time.monotonic()
  if self.kind=='fairy':
   h=Hybrid(self.engine,self.level,self.seconds,self.nodes);m=h.choose(g,cancel);info=h.last_info
  else:
   bot=(self.legacy.Search if self.kind=='legacy' else Search)(self.level,self.seconds if self.seconds is not None else .12)
   m=bot.choose(g) if self.kind=='legacy' else bot.choose(g,cancel)
   info=dict(mode=self.kind,seconds=time.monotonic()-begin,nodes=bot.nodes,calls=0)
  return m,info
 def reset(self):
  if self.engine:self.engine.new_game()
 def close(self):
  if self.engine:self.engine.close()

def board_eval(e):return r.evaluate(r.state_from_dict(e),0)
def material(e):return sum((1 if p.isupper() else -1)*r.VAL[p.lower()] for p in e['board'] if p!='.')

def summarise_game(g,settings,thinking,stopped=False):
 events=g.log
 begin=next((e for e in events if e['phase']=='charge'),None)
 end=next((e for e in events if e['phase']=='charge_end'),None)
 normal=next((e for e in events if e['phase']=='response'),None)
 counter=next((e for e in events if e['phase']=='counter_end'),None)
 if begin and g.winner and not counter:counter=events[-1]
 def delta(a,b,fun=board_eval):return fun(b)-fun(a) if a and b else None
 return dict(seed=g.seed,white=settings['white'],black=settings['black'],winner=g.winner,
  reason=g.reason or ('unfinished (cancelled)' if stopped else 'unfinished (move limit)'),
  victory_phase=('after charge' if begin else 'before charge') if g.winner in ('white','black') else None,
  charge_move=begin['move'] if begin else None,
  knights_at_charge=begin['board'].count('n') if begin else None,
  housecarls_at_charge=begin['board'].count('H') if begin else None,
  knights_at_end=g.s.b.count('n'),housecarls_at_end=g.s.b.count('H'),
  housecarl_captures=sum(e.get('piece')=='H' and e.get('captured','.')!='.' for e in events)+sum(e.get('event',{}).get('unit')=='H' and 'captured' in e.get('event',{}) for e in events),
  housecarls_captured=sum(e.get('captured')=='H' for e in events),
  charge_material_delta=delta(begin,end,material),charge_positional_delta=delta(begin,end),
  normal_response_delta=delta(end,normal),knight_bonus_delta=delta(normal,counter),
  full_sequence_delta=delta(begin,counter),thinking=thinking,replay=g.export())

def run(count,seed,limit,level=2,seconds=None,white='fairy',black='fairy',nodes=None,cancel=None,progress=None,bonus_mode='knight_pawn'):
 if white not in ('fairy','light','legacy') or black not in ('fairy','light','legacy'):raise ValueError('Unknown opponent')
 if bonus_mode!='knight_pawn':raise ValueError('Unsupported pre-release experimental Norman bonus ruleset')
 if level not in LEVELS and level!=BENCHMARK_LEVEL_3:raise ValueError('Unknown simulation difficulty')
 if level==BENCHMARK_LEVEL_3 and (white!='fairy' or black!='fairy'):
  raise ValueError('Benchmark Level 3 requires Fairy-Stockfish on both sides')
 if count<1 or limit<1:raise ValueError('Game count and move limit must be positive')
 settings=dict(count=count,seed=seed,limit=limit,level=level,seconds=seconds,white=white,black=black,nodes=nodes,bonus_mode=bonus_mode)
 bots={0:Opponent(white,level,seconds,nodes),1:Opponent(black,level,seconds,nodes)}
 results=[];cancel=cancel or threading.Event()
 try:
  for number in range(count):
   if cancel.is_set():break
   for bot in bots.values():bot.reset()
   g=Game(seed+number,bonus_mode=bonus_mode);thinking=[]
   while not g.winner and g.white_move<=limit and not cancel.is_set():
    g.start_turn()
    if g.winner:break
    actor=g.side
    try:m,info=bots[actor].choose(g,cancel)
    except SearchCancelled:break
    if cancel.is_set():break
    if m is None:raise RuntimeError('Opponent returned no move in a live game')
    g.move(m);thinking.append(dict(side=actor,**info))
   results.append(summarise_game(g,settings,thinking,cancel.is_set()))
   if progress:progress(len(results))
 finally:
  for bot in bots.values():bot.close()
 outcomes=Counter(f"{g['reason']}: {g['winner'] or 'none'}" for g in results)
 thoughts=[t for g in results for t in g['thinking']]
 return dict(format='hastings-batch-3',ruleset=r.RULESET+'-'+bonus_mode,settings=settings,completed_games=len(results),
  outcomes=dict(outcomes),victory_phase=dict(Counter(g['victory_phase'] for g in results if g['victory_phase'])),
  charge_move_histogram=dict(sorted(Counter(g['charge_move'] for g in results if g['charge_move']).items())),
  charge_not_reached=sum(g['charge_move'] is None for g in results),
  knights_at_charge=dict(Counter(g['knights_at_charge'] for g in results if g['charge_move'])),
  mean_knights_at_charge=statistics.mean(g['knights_at_charge'] for g in results if g['charge_move']) if any(g['charge_move'] for g in results) else None,
  engine_calls=sum(t['calls'] for t in thoughts),total_thinking_seconds=sum(t['seconds'] for t in thoughts),
  mean_thinking_seconds=statistics.mean(t['seconds'] for t in thoughts) if thoughts else 0,
  max_thinking_seconds=max((t['seconds'] for t in thoughts),default=0),games=results)

if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--games',type=int,default=2);a.add_argument('--seed',type=int,default=230926)
 a.add_argument('--limit',type=int,default=80);a.add_argument('--level',default='3',help='Public 1–10 or benchmark-3')
 a.add_argument('--seconds',type=float);a.add_argument('--nodes',type=int)
 a.add_argument('--white',choices=['fairy','light','legacy'],default='fairy');a.add_argument('--black',choices=['fairy','light','legacy'],default='fairy')
 a.add_argument('--output',default='batch.json');args=a.parse_args()
 args.level=BENCHMARK_LEVEL_3 if args.level.lower() in ('benchmark-3',BENCHMARK_LEVEL_3.lower()) else int(args.level)
 d=run(args.games,args.seed,args.limit,args.level,args.seconds,args.white,args.black,args.nodes,progress=lambda n:print('Completed',n,flush=True),bonus_mode=args.bonus_mode)
 Path(args.output).write_text(json.dumps(d,indent=2),encoding='utf8')
 print({k:v for k,v in d.items() if k!='games'})
