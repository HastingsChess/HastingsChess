"""Dedicated post-game evaluator; no Tk calls and no live-game analysis."""
import queue,threading
from engine_uci import FairyEngine,SearchCancelled
from replay_analysis import ReplayAnalyzer

class ReplayWorker:
    def __init__(self,results):
        self.jobs=queue.Queue();self.results=results;self.cancel=threading.Event()
        self.thread=threading.Thread(target=self._run,daemon=True);self.thread.start()

    def request(self,token,replay,index):
        if self.cancel.is_set():return
        # Navigation takes precedence over old, unstarted requests.
        try:
            while True:self.jobs.get_nowait()
        except queue.Empty:pass
        self.jobs.put((token,replay,index))

    def _run(self):
        engine=None
        try:
            while not self.cancel.is_set():
                job=self.jobs.get()
                if job is None:break
                token,replay,index=job
                try:
                    if engine is None:engine=FairyEngine()
                    score=ReplayAnalyzer(engine).event(replay,index,self.cancel)
                    if not self.cancel.is_set():self.results.put(('replay_eval',token,(id(replay),index,score,None)))
                except SearchCancelled:break
                except Exception as exc:
                    if engine:engine.close();engine=None
                    if not self.cancel.is_set():self.results.put(('replay_eval',token,(id(replay),index,None,str(exc))))
        finally:
            if engine:engine.close()

    def close(self):
        self.cancel.set();self.jobs.put(None)
