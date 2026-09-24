"""Reproducible self-play; move limits remain unfinished, never wins."""
import argparse,json,statistics
from collections import Counter
from pathlib import Path
from game import Game
from ai import Search
import rules as r

def run(count,seed,limit,level=1,seconds=.08):
 results=[]
 for number in range(count):
  g=Game(seed+number)
  ai=Search(level,seconds)
  while not g.winner and g.white_move<=limit:
   if g.side==0:g.start_turn()
   if g.winner:break
   m=ai.choose(g)
   if m is None:
    g._terminal(g.side);break
   g.move(m)
  events=g.log
  charge=next((e['move'] for e in events if e['phase']=='charge'),None)
  opening=next((r.evaluate(_state_from_event(e),0) for e in events if e['phase']=='charge'),None)
  at_charge=next((e for e in events if e['phase']=='charge'),None)
  after=next((r.evaluate(_state_from_event(e),0) for e in reversed(events) if e['phase']=='charge'),None)
  results.append(dict(seed=g.seed,winner=g.winner,reason=g.reason or 'unfinished (move limit)',
    charge_move=charge,knights_at_charge=at_charge['board'].count('n') if at_charge else None,
    housecarls_at_charge=at_charge['board'].count('H') if at_charge else None,
    knights_at_end=g.s.b.count('n'),housecarls_at_end=g.s.b.count('H'),
    charge_eval_before=opening,charge_eval_after=after,actions=len(events)-1,
    replay=g.export()))
 outcomes=Counter((g['reason'],g['winner']) for g in results)
 return dict(format='hastings-batch-1',settings=dict(count=count,seed=seed,limit=limit,level=level,seconds=seconds),
  outcomes={f'{reason}: {winner or "none"}':n for (reason,winner),n in outcomes.items()},
  charge_move_histogram=dict(sorted(Counter(g['charge_move'] for g in results if g['charge_move']).items())),
  charge_not_reached=sum(g['charge_move'] is None for g in results),
  surviving_knights=dict(Counter(g['knights_at_charge'] for g in results if g['charge_move'])),
  housecarls_remaining=dict(Counter(g['housecarls_at_charge'] for g in results if g['charge_move'])),
  mean_charge_delta=statistics.mean(g['charge_eval_after']-g['charge_eval_before'] for g in results if g['charge_eval_before'] is not None) if any(g['charge_eval_before'] is not None for g in results) else None,
  games=results)

def _state_from_event(e):
 s=r.State();s.b=list(e['board']);return s

if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--games',type=int,default=10);a.add_argument('--seed',type=int,default=230926);a.add_argument('--limit',type=int,default=60);a.add_argument('--level',type=int,default=1);a.add_argument('--seconds',type=float,default=.08);a.add_argument('--output',default='batch.json')
 args=a.parse_args();Path(args.output).write_text(json.dumps(run(args.games,args.seed,args.limit,args.level,args.seconds),indent=2),encoding='utf8')
