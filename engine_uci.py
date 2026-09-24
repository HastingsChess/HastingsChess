"""Real, bounded Fairy-Stockfish UCI process. No network is used during play."""
from dataclasses import dataclass
from pathlib import Path
import os,platform,queue,re,subprocess,threading,time,sys
import rules as r

BASE=Path(__file__).resolve().parent

class EngineError(RuntimeError):pass
class IncompatiblePosition(EngineError):pass
class SearchCancelled(EngineError):pass

def engine_filename(system=None,machine=None):
    system=sys.platform if system is None else system
    machine=platform.machine().lower() if machine is None else machine.lower()
    if system=='win32':return 'fairy-stockfish.exe'
    if system=='darwin':
        if machine=='arm64':return 'fairy-stockfish-macos-arm64'
        if machine=='x86_64':return 'fairy-stockfish-macos-x86_64'
        raise EngineError('Unsupported macOS CPU: '+machine)
    if system.startswith('linux'):return 'fairy-stockfish-linux'
    raise EngineError('Unsupported operating system: '+system)

def default_engine():return BASE/'engine'/engine_filename()

def uci_move(m):return r.symbol(m[0])+r.symbol(m[1])+m[2]

def compatible(s,side):
    # A side that has supposedly just moved cannot have left itself in check.
    # The Hastings charge and repeated Black turns can break that assumption.
    if s.b.count('K')!=1 or s.b.count('k')!=1:return False
    if r.in_check(s,1-side):return False
    if any(s.b[i]=='p' for i in range(8)) or any(s.b[i]=='P' for i in range(56,64)):return False
    return True

def fen(s,side,fullmove=1):
    if not compatible(s,side):raise IncompatiblePosition('Non-moving king is in check, or an unpromoted pawn is on a back rank; Python must resolve this special position.')
    rows=[]
    for rank in range(7,-1,-1):
        row='';empty=0
        for p in s.b[rank*8:rank*8+8]:
            if p=='.':empty+=1
            else:
                if empty:row+=str(empty);empty=0
                row+=p
        if empty:row+=str(empty)
        rows.append(row)
    rights=''.join(k for k in 'KQkq' if s.castle.get(k)) or '-'
    return '/'.join(rows)+f' {"w" if side==0 else "b"} {rights} {r.symbol(s.ep) if s.ep>=0 else "-"} {s.hm} {max(1,fullmove)}'

@dataclass
class Analysis:
    move:tuple
    cp:int
    depth:int
    nodes:int
    pv:tuple
    mate:int|None=None

class FairyEngine:
    def __init__(self,path=None,hash_mb=64):
        self.path=Path(path) if path else default_engine()
        if not self.path.is_file():raise EngineError(f'Fairy-Stockfish missing: {self.path}. Use Repair engine in the application or SETUP_ENGINE.bat.')
        self.lines=queue.Queue();self.lock=threading.Lock();self.calls=0;self.total_nodes=0;self.name=''
        kwargs={'creationflags':subprocess.CREATE_NO_WINDOW} if os.name=='nt' else {}
        # Fairy-Stockfish v14's `load` parser splits its arguments on whitespace,
        # even when Popen correctly quotes a Windows executable/config path.
        # Passing an absolute config path therefore FAILS when Hastings Chess is
        # extracted under e.g. `C:\Users\Nick\Hastings Chess\...`.  Launch with
        # the engine folder as cwd and the whitespace-free config basename instead.
        # The executable's own absolute path is safely quoted by subprocess.
        config_dir=BASE/'engine'
        if not (config_dir/'hastings.ini').is_file():
            raise EngineError('Missing engine/hastings.ini. Extract the full Hastings Chess ZIP.')
        try:
            self.process=subprocess.Popen([str(self.path.resolve()),'load','hastings.ini'],
                stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                text=True,encoding='utf-8',errors='replace',bufsize=1,cwd=str(config_dir),**kwargs)
        except OSError as e:raise EngineError(f'Cannot start {self.path.name}: {e}') from e
        def reader():
            try:
                for line in self.process.stdout:self.lines.put(line.strip())
            finally:self.lines.put(None)
        self.thread=threading.Thread(target=reader,daemon=True);self.thread.start()
        try:
            self.send('uci');lines=self._until('uciok',10)
            self.name=next((x[8:] for x in lines if x.startswith('id name ')),'unknown')
            if not any('UCI_Variant' in x and ' var hastings' in x for x in lines):raise EngineError('Engine did not load the Hastings custom-piece variant (check engine/hastings.ini and extract the full ZIP).')
            if 'Fairy-Stockfish' not in self.name:raise EngineError('Unexpected engine identity: '+self.name)
            for name,value in [('UCI_Variant','hastings'),('Threads',1),('Hash',hash_mb),('Use NNUE','false'),('UCI_AnalyseMode','true')]:
                self.send(f'setoption name {name} value {value}')
            self.ready()
        except Exception:self.close();raise

    def send(self,line):
        try:self.process.stdin.write(line+'\n');self.process.stdin.flush()
        except (BrokenPipeError,OSError,ValueError) as e:raise EngineError('Fairy-Stockfish process stopped unexpectedly') from e

    def _until(self,prefix,timeout,cancel=None):
        end=time.monotonic()+timeout;lines=[];stopping=False
        while True:
            if cancel and cancel.is_set() and not stopping:
                self.send('stop');stopping=True
            remaining=end-time.monotonic()
            if remaining<=0:self.close();raise EngineError('Fairy-Stockfish timed out; stopped safely. Choose Repair engine or the lightweight opponent.')
            try:line=self.lines.get(timeout=min(.05,remaining))
            except queue.Empty:continue
            if line is None:raise EngineError('Fairy-Stockfish exited unexpectedly')
            lines.append(line)
            if line.startswith(prefix):
                if stopping:raise SearchCancelled('Search cancelled')
                return lines

    def ready(self):self.send('isready');self._until('readyok',5)

    def analyse(self,s,side,fullmove=1,multipv=1,movetime=150,nodes=None,depth=None,searchmoves=None,cancel=None):
        position=fen(s,side,fullmove)
        legal=r.legal(s,side);mapping={uci_move(m):m for m in legal}
        if not legal:return []
        if cancel and cancel.is_set():raise SearchCancelled('Search cancelled')
        with self.lock:
            self.send(f'setoption name MultiPV value {min(multipv,len(legal))}')
            self.send('position fen '+position)
            # Fixed node limits support reproducible benchmark runs. GUI uses time.
            cmd='go'+(f' nodes {max(1,nodes)}' if nodes is not None else f' movetime {max(1,int(movetime))}')
            if depth:cmd+=f' depth {depth}'
            if searchmoves:cmd+=' searchmoves '+' '.join(uci_move(m) for m in searchmoves)
            self.send(cmd);lines=self._until('bestmove',max(10,movetime/1000+5),cancel)
            self.calls+=1;by_rank={};best=''
            for line in lines:
                if line.startswith('bestmove '):best=line.split()[1];continue
                t=line.split()
                if 'score' not in t or 'pv' not in t:continue
                try:
                    kind=t[t.index('score')+1];value=int(t[t.index('score')+2])
                    rank=int(t[t.index('multipv')+1]) if 'multipv' in t else 1
                    pv=tuple(t[t.index('pv')+1:]);d=int(t[t.index('depth')+1]);n=int(t[t.index('nodes')+1]) if 'nodes' in t else 0
                    if not pv or pv[0] not in mapping:raise EngineError('Engine returned a move outside Hastings legality: '+str(pv))
                    cp=value if kind=='cp' else (100000-abs(value)*100)*(1 if value>0 else -1)
                    # Bound scores are useful ordering hints, but prefer latest completed line.
                    by_rank[rank]=Analysis(mapping[pv[0]],cp,d,n,pv,value if kind=='mate' else None)
                except (ValueError,IndexError):continue
            if best not in mapping:raise EngineError('Engine bestmove is not Hastings-legal: '+best)
            if searchmoves and mapping[best] not in searchmoves:raise EngineError('Engine ignored restricted root moves')
            if not by_rank:raise EngineError('Engine supplied a move without an evaluation')
            self.total_nodes+=max((a.nodes for a in by_rank.values()),default=0)
            # Stockfish MultiPV=1 strength controls are not used; root eval determines choice.
            return [by_rank[k] for k in sorted(by_rank)]

    def legal_moves(self,s,side):
        """Real engine perft for differential tests; Python remains authoritative."""
        position=fen(s,side)
        with self.lock:
            self.send('position fen '+position);self.send('go perft 1')
            lines=self._until('Nodes searched:',10)
        return {line.split(':')[0] for line in lines if re.match(r'^[a-h][1-8][a-h][1-8][qrbnh]?: ',line)}

    def new_game(self):
        with self.lock:self.send('ucinewgame');self.ready()

    def close(self):
        p=getattr(self,'process',None)
        if not p:return
        try:
            if p.poll() is None:
                self.send('quit')
                try:p.wait(timeout=1)
                except subprocess.TimeoutExpired:p.kill();p.wait(timeout=1)
        except (OSError,EngineError):pass
        for stream in (p.stdin,p.stdout):
            try:stream.close()
            except (OSError,ValueError):pass
