"""One background engine owner. Workers never access Tk variables/widgets."""
import queue,threading,time
from ai import Search
from engine_uci import FairyEngine,EngineError,SearchCancelled
from hybrid import Hybrid

class EngineWorker:
    def __init__(self):
        self.jobs=queue.Queue();self.results=queue.Queue();self.engine=None
        self.thread=threading.Thread(target=self._run,daemon=True);self.thread.start()
    def submit(self,token,game,mode,level,cancel):self.jobs.put(('move',token,game,mode,level,cancel))
    def probe(self,token,cancel,repair=False):self.jobs.put(('repair' if repair else 'probe',token,None,'Fairy-Stockfish hybrid',1,cancel))
    def _run(self):
        while True:
            job=self.jobs.get()
            if job is None:break
            kind,token,game,mode,level,cancel=job
            if cancel.is_set():continue
            try:
                if kind=='repair':
                    if self.engine:self.engine.close();self.engine=None
                    from setup_engine import setup
                    setup(lambda text:self.results.put(('status',token,text)))
                if mode=='Fairy-Stockfish hybrid' and self.engine is None:
                    self.results.put(('status',token,'Starting Fairy-Stockfish…'))
                    self.engine=FairyEngine()
                if kind in ('probe','repair'):
                    self.results.put(('ready',token,self.engine.name));continue
                if mode=='Fairy-Stockfish hybrid':
                    opponent=Hybrid(self.engine,level=level);move=opponent.choose(game,cancel)
                    info=opponent.last_info
                else:
                    start=time.monotonic();opponent=Search(min(level,4),.2+.4*min(level,4));move=opponent.choose(game,cancel)
                    info=dict(mode='Lightweight custom',seconds=time.monotonic()-start,nodes=opponent.nodes,calls=0)
                if not cancel.is_set():self.results.put(('move',token,(move,info)))
            except SearchCancelled:pass
            except Exception as e:
                if self.engine:self.engine.close();self.engine=None
                if not cancel.is_set():self.results.put(('error',token,str(e)))
        if self.engine:self.engine.close()
    def close(self):self.jobs.put(None)
