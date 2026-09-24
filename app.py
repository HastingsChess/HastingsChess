"""Hastings Chess desktop app. Offline, standard-library Tk interface."""
import json, random, threading, time, queue, uuid, sys
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog, font
import rules as r
from game import Game,replay_valid
from workers import EngineWorker
from engine_uci import EngineError
from settings import Settings,SAXON_RATING
from hybrid import LEVEL_NAMES
from replay_analysis import display,white_fraction
from replay_worker import ReplayWorker

ROOT=Path(__file__).resolve().parent
SYMBOL={'K':'♔','Q':'♕','R':'♖','B':'♗','N':'♘','P':'♙',
        'k':'♚','q':'♛','r':'♜','b':'♝','n':'♞','p':'♟'}

class App:
 def __init__(self,root):
    self.root=root;root.title('Hastings Chess — Random Catastrophes');root.minsize(640,580)
    self.settings=Settings();self.g=Game(random.randrange(1,2**30));self.mode=tk.StringVar(value='Saxons vs computer')
    self.game_id=uuid.uuid4().hex;self.game_rated=True;self.rating_change=None
    self.engine_mode=tk.StringVar(value='Fairy-Stockfish hybrid');self.engine_status=tk.StringVar(value='Fairy-Stockfish selected')
    self.worker=EngineWorker();self.cancel=threading.Event();self.closed=False;self.paused=False;self.sim_cancel=None
    self.level=tk.IntVar(value=self.settings.data['difficulty']);self.delay=tk.IntVar(value=350)
    self.level_text=tk.StringVar(value=self.difficulty_label(self.level.get()))
    self.selected=None;self.flip=False;self.replay=None;self.replay_index=0;self.replay_bundle=[]
    self.busy=False;self.generation=0;self.playing=False;self.silent=tk.BooleanVar(value=False)
    self.replay_worker=None;self.replay_cache={};self.eval_canvas=None;self.eval_label=None
    root.configure(bg='#15242b')
    families=set(font.families(root));self.piece_font='Segoe UI Symbol' if 'Segoe UI Symbol' in families else 'DejaVu Sans'
    self.tick=None;self.piece_images={}
    bar=ttk.Frame(root,padding=8);bar.pack(fill='x')
    ttk.Button(bar,text='New battle',command=self.new).pack(side='left')
    self.mode_box=ttk.Combobox(bar,textvariable=self.mode,values=['Saxons vs computer','Normans vs computer','Computer vs computer','Two humans'],state='readonly',width=21);self.mode_box.pack(side='left',padx=5)
    self.mode_box.bind('<<ComboboxSelected>>',lambda e:self.mode_changed())
    ttk.Label(bar,text='Difficulty').pack(side='left')
    self.level_box=ttk.Combobox(bar,textvariable=self.level_text,
          values=[self.difficulty_label(i) for i in range(1,11)],state='readonly',width=20)
    self.level_box.pack(side='left',padx=5);self.level_box.bind('<<ComboboxSelected>>',self.difficulty_changed)
    tools=ttk.Frame(root,padding=(8,0,8,5));tools.pack(fill='x')
    ttk.Button(tools,text='Flip',command=self.flip_board).pack(side='left',padx=4)
    ttk.Button(tools,text='Undo',command=self.undo).pack(side='left')
    ttk.Button(tools,text='Save',command=self.save).pack(side='left',padx=4)
    ttk.Button(tools,text='Open replay',command=self.open_replay).pack(side='left')
    self.review_button=ttk.Button(tools,text='Review finished',command=self.review_finished)
    self.review_button.pack(side='left',padx=4)
    ttk.Button(tools,text='Simulate',command=self.simulate).pack(side='left',padx=4)
    ttk.Button(tools,text='Pause / resume',command=self.toggle_pause).pack(side='left',padx=4)
    engrow=ttk.Frame(root,padding=(8,0,8,5));engrow.pack(fill='x')
    self.engine_box=ttk.Combobox(engrow,textvariable=self.engine_mode,values=['Fairy-Stockfish hybrid','Lightweight custom'],state='readonly',width=24)
    self.engine_box.pack(side='left');self.engine_box.bind('<<ComboboxSelected>>',lambda e:self.mode_changed())
    ttk.Button(engrow,text='Check engine' if getattr(sys,'frozen',False) or sys.platform=='darwin' else 'Repair engine',command=self.repair_engine).pack(side='left',padx=6)
    ttk.Label(engrow,textvariable=self.engine_status,wraplength=250).pack(side='left',fill='x',expand=True)
    self.rules_mode=tk.StringVar(value='Knights + pawns')
    rulesrow=ttk.Frame(root,padding=(8,0,8,5));rulesrow.pack(fill='x')
    ttk.Label(rulesrow,text='Norman bonus rules for new battles:').pack(side='left')
    self.rules_box=ttk.Combobox(rulesrow,textvariable=self.rules_mode,
       values=['Knights + pawns','Experimental: any piece'],state='readonly',width=25)
    self.rules_box.pack(side='left',padx=8)
    body=ttk.Frame(root,padding=8);body.pack(fill='both',expand=True);self.body=body
    self.canvas=tk.Canvas(body,bg='#17262e',highlightthickness=0)
    self.canvas.pack(side='left',fill='both',expand=True)
    self.canvas.bind('<Configure>',lambda e:self.draw());self.canvas.bind('<Button-1>',self.click)
    panel=ttk.Frame(body,width=205);panel.pack(side='right',fill='y',padx=(8,0));panel.pack_propagate(False);self.panel=panel
    self.replay_selector=ttk.Combobox(panel,state='readonly',width=22)
    self.replay_selector.pack(fill='x',pady=(0,5));self.replay_selector.bind('<<ComboboxSelected>>',self.choose_replay)
    self.status=ttk.Label(panel,text='',wraplength=215,justify='left',font=('Segoe UI',11,'bold'));self.status.pack(anchor='w',pady=(0,12))
    self.ratings=ttk.Label(panel,text='',wraplength=205,justify='left');self.ratings.pack(anchor='w')
    self.rating_detail=ttk.Label(panel,text='',wraplength=205,justify='left');self.rating_detail.pack(anchor='w',pady=(0,7))
    self.tip=None;self.ratings.bind('<Enter>',self.rating_tooltip);self.ratings.bind('<Leave>',self.hide_rating_tooltip)
    self.odds=ttk.Label(panel,text='',wraplength=215,justify='left');self.odds.pack(anchor='w')
    self.knights=ttk.Label(panel,text='');self.knights.pack(anchor='w',pady=6)
    self.event_detail=ttk.Label(panel,text='',wraplength=195,justify='left');self.event_detail.pack(anchor='w',fill='x')
    ttk.Label(panel,text='The chronicle',font=('Segoe UI',10,'bold')).pack(anchor='w',pady=(10,2))
    self.events=tk.Listbox(panel,selectmode='browse',font=('Segoe UI',9),exportselection=False)
    self.events.pack(fill='both',expand=True);self.events.bind('<<ListboxSelect>>',self.select_event)
    rep=ttk.Frame(panel);rep.pack(fill='x',pady=5)
    for caption,fun in [('Back',self.previous),('Next',self.next),('Charge',self.jump_charge),('Live',self.live)]:
        ttk.Button(rep,text=caption,command=fun,width=5).pack(side='left',expand=True,fill='x')
    ttk.Label(panel,text='Replay: select an event. Bonus actions have their own entries.',wraplength=205).pack(anchor='w')
    self.refresh();root.protocol('WM_DELETE_WINDOW',self.close);self.tick=root.after(100,self.pump)

 def invalidate(self):
    self.cancel.set();self.cancel=threading.Event();self.generation+=1;self.busy=False;self.selected=None
 def new(self):
    self.invalidate();self.leave_replay();self.g=Game(random.randrange(1,2**30),bonus_mode=self.selected_rules());self.paused=False
    self.game_id=uuid.uuid4().hex;self.game_rated=self.mode.get()!='Computer vs computer';self.rating_change=None
    self.g.start_turn();self.refresh()
 def difficulty_label(self,n):return f'{n}. {LEVEL_NAMES[n-1]}'
 def difficulty_changed(self,event=None):
    try:n=int(self.level_text.get().split('.')[0]);self.settings.set_difficulty(n)
    except (ValueError,IndexError,OSError) as exc:
     messagebox.showerror('Difficulty',str(exc));return
    self.level.set(n);self.invalidate();self.refresh()
 def selected_rules(self):
    return 'any_piece' if self.rules_mode.get()=='Experimental: any piece' else 'knight_pawn'
 def mode_changed(self):
    if self.mode.get()=='Computer vs computer':self.game_rated=False
    self.invalidate();self.engine_status.set(self.engine_mode.get()+' selected');self.refresh()
 def rating_tooltip(self,event):
    self.hide_rating_tooltip()
    self.tip=tk.Toplevel(self.root);self.tip.wm_overrideredirect(True)
    self.tip.wm_geometry(f'+{event.x_root+10}+{event.y_root+16}')
    ttk.Label(self.tip,text='Saxon rating is historically fixed at 1066.\nPerformance adjustments are unavailable under current military doctrine.',padding=6).pack()
 def hide_rating_tooltip(self,event=None):
    if self.tip:self.tip.destroy();self.tip=None
 def repair_engine(self):
    self.invalidate();self.busy=True;self.engine_status.set('Checking engine…')
    self.worker.probe(self.generation,self.cancel,repair=not getattr(sys,'frozen',False) and sys.platform!='darwin')
 def toggle_pause(self):
    self.paused=not self.paused
    if self.paused:self.invalidate()
    self.refresh()
 def close(self):
    self.closed=True;self.cancel.set()
    self.leave_replay();self.hide_rating_tooltip()
    if self.sim_cancel:self.sim_cancel.set()
    self.worker.close()
    if self.tick:
     try:self.root.after_cancel(self.tick)
     except tk.TclError:pass
    self.root.destroy()
 def flip_board(self):self.flip=not self.flip;self.draw()
 def undo(self):
    self.invalidate();self.leave_replay()
    if self.g.undo():
     # Return control to the selected human instead of instantly replaying AI.
     while self.g.history and not self.active() and self.mode.get() not in ('Computer vs computer','Two humans'):
      self.g.undo()
     self.paused=True;self.refresh()
 def save(self):
    p=filedialog.asksaveasfilename(defaultextension='.json',filetypes=[('Hastings replay','*.json')])
    if p:
     try:Path(p).write_text(json.dumps(self.replay or self.g.export(),indent=2),encoding='utf-8')
     except OSError as e:messagebox.showerror('Save failed',str(e))
 def open_replay(self):
    p=filedialog.askopenfilename(filetypes=[('Hastings replay','*.json')])
    if not p:return
    try:self.load_replay_data(json.loads(Path(p).read_text(encoding='utf-8')))
    except (OSError,ValueError,KeyError,TypeError) as e:messagebox.showerror('Replay error',str(e));return
    self.invalidate();self.replay_index=0;self.refresh(reset=False)
 def review_finished(self):
    if not self.g.winner:return
    self.load_replay_data(self.g.export());self.invalidate()
    self.replay_index=len(self.replay['events'])-1;self.refresh(reset=False)
 def load_replay_data(self,data):
    if data.get('format') in ('hastings-batch-1','hastings-batch-2','hastings-batch-3'):
     games=data.get('games',[])
     if not games or len(games)>1000:raise ValueError('Batch must contain 1–1000 recorded games')
     bundle=[replay_valid(g['replay']) for g in games]
    else:bundle=[replay_valid(data)]
    self.leave_replay();self.replay_bundle=bundle;self.replay=bundle[0]
    self.replay_selector.config(values=[f"{i+1}: seed {g['seed']} — {g.get('winner') or 'unfinished'}" for i,g in enumerate(bundle)])
    self.replay_selector.current(0)
 def choose_replay(self,event=None):
    i=self.replay_selector.current()
    if 0<=i<len(self.replay_bundle):
     self.invalidate();self.leave_replay();self.replay=self.replay_bundle[i];self.replay_index=0;self.refresh(reset=False)
 def leave_replay(self):
    if self.replay_worker:self.replay_worker.close();self.replay_worker=None
    self.replay_cache.clear()
    if self.eval_canvas:self.eval_canvas.destroy();self.eval_canvas=None
    if self.eval_label:self.eval_label.destroy();self.eval_label=None
    self.replay=None
 def analyse_replay(self):
    if not self.replay or not self.replay.get('winner') or self.replay.get('format')!='hastings-chess-3':return
    if self.eval_canvas is None:
     self.eval_canvas=tk.Canvas(self.body,width=54,bg='#17262e',highlightthickness=0)
     self.eval_canvas.pack(side='left',fill='y',before=self.canvas)
     self.eval_label=ttk.Label(self.panel,text='',wraplength=205,justify='left')
     self.eval_label.pack(anchor='w',before=self.odds,pady=(0,8))
    if self.replay_worker is None:self.replay_worker=ReplayWorker(self.worker.results)
    key=(id(self.replay),self.replay_index)
    if key not in self.replay_cache:
     self.replay_cache[key]=(None,None)
     self.replay_worker.request(self.generation,self.replay,self.replay_index)
 def draw_eval(self):
    if self.eval_canvas is None:return
    c=self.eval_canvas;c.delete('all');score,error=self.replay_cache.get((id(self.replay),self.replay_index),(None,None))
    h=max(100,c.winfo_height());top=52;bottom=h-52;f=white_fraction(score)
    c.create_text(27,24,text='BLACK\nNormans',fill='#eee4d3',font=('Segoe UI',8,'bold'),justify='center')
    c.create_rectangle(11,top,43,bottom,fill='#1d262a',outline='#bd9d66',width=2)
    split=bottom-(bottom-top)*f
    c.create_rectangle(13,split,41,bottom-2,fill='#f6f0da',outline='')
    c.create_text(27,h-24,text='WHITE\nSaxons',fill='#eee4d3',font=('Segoe UI',8,'bold'),justify='center')
    self.eval_label.config(text=('Analysis unavailable: '+error if error else
                         display(score)+((' · '+score.note) if score else '')))
 def simulate(self):
    from simulate import run
    if self.sim_cancel:
     self.sim_cancel.set();return
    count=simpledialog.askinteger('Self-play','Games (1–1000):',initialvalue=10,minvalue=1,maxvalue=1000,parent=self.root)
    if count is None:return
    seed=simpledialog.askinteger('Reproducible self-play','First seed:',initialvalue=230926,minvalue=0,parent=self.root)
    if seed is None:return
    path=filedialog.asksaveasfilename(defaultextension='.json',filetypes=[('JSON statistics and replays','*.json')])
    if not path:return
    self.paused=True;self.invalidate();self.sim_cancel=threading.Event()
    mode='fairy' if self.engine_mode.get()=='Fairy-Stockfish hybrid' else 'light'
    level=self.level.get();cancel=self.sim_cancel
    self.status.config(text='Self-play running. Click Simulate again to stop after the current action.')
    def work():
     try:
      data=run(count,seed,80,level=level,white=mode,black=mode,cancel=cancel,bonus_mode=self.g.bonus_mode,
               progress=lambda n:self.worker.results.put(('simulation_progress',-1,f'{n}/{count} games complete')))
      Path(path).write_text(json.dumps(data,indent=2),encoding='utf-8')
      self.worker.results.put(('simulation_done',-1,f"Saved {data['completed_games']} games to {path}.\n"+str(data['outcomes'])))
     except Exception as e:self.worker.results.put(('simulation_error',-1,str(e)))
    threading.Thread(target=work,daemon=True).start()
 def entries(self):return self.replay['events'] if self.replay else self.g.log
 def previous(self):self.replay_index=max(0,self.replay_index-1);self.analyse_replay();self.draw()
 def next(self):self.replay_index=min(len(self.entries())-1,self.replay_index+1);self.analyse_replay();self.draw()
 def jump_charge(self):
    for i,e in enumerate(self.entries()):
        if e['phase']=='charge':self.replay_index=i;self.analyse_replay();self.draw();return
 def live(self):
    if self.replay:self.leave_replay()
    self.replay_index=len(self.g.log)-1;self.refresh(reset=False)
 def select_event(self,event):
    v=self.events.curselection()
    if v:self.replay_index=v[0];self.analyse_replay();self.draw()
 def active(self):
    if self.replay or self.g.winner:return False
    mode=self.mode.get()
    return mode=='Two humans' or (mode=='Saxons vs computer' and self.g.side==0) or (mode=='Normans vs computer' and self.g.side==1)
 def refresh(self,reset=True):
    if self.g.winner and self.game_rated and self.rating_change is None:
     try:
      self.rating_change=self.settings.record(self.game_id,self.g.winner)
     except OSError as exc:
      self.game_rated=False;messagebox.showerror('Rating could not be saved',str(exc))
    e=self.entries();self.events.delete(0,'end')
    for event in e:self.events.insert('end',event['label'])
    if reset:self.replay_index=len(e)-1
    self.replay_index=max(0,min(self.replay_index,len(e)-1))
    self.events.selection_set(self.replay_index);self.events.see(self.replay_index)
    status=('Replay' if self.replay else f'{"Saxons" if self.g.side==0 else "Normans"} to act — {self.g.phase}')
    if self.g.winner and not self.replay:status=f'{self.g.winner.title()} — {self.g.reason}'
    if self.paused:status+=' [paused]'
    if self.busy:status+=' — thinking…'
    if self.replay and self.replay.get('format')=='hastings-chess-1':status+=' — legacy rules (view only)'
    elif not self.replay:status+=' · '+('any-piece bonus' if self.g.bonus_mode=='any_piece' else 'knight/pawn bonus')
    self.status.config(text=status)
    self.review_button.state(['!disabled'] if self.g.winner else ['disabled'])
    self.ratings.config(text=f'Normans — Elo {self.settings.norman_elo}\nSaxons — Elo {SAXON_RATING}')
    if self.rating_change:
     before,after=self.rating_change
     self.rating_detail.config(text=f'Normans: {before} → {after} ({after-before:+d})\nSaxons: 1066 → 1066 (+0)')
    else:self.rating_detail.config(text='')
    self.odds.config(text=f'Upcoming charge chance: {self.g.odds():.0%} (conditional). White move {self.g.white_move}.' if not self.replay else 'Saved battle')
    self.knights.config(text=f'Norman knights surviving: {self.g.s.b.count("n")}')
    self.analyse_replay()
    self.draw()
 def draw(self):
    c=self.canvas;c.delete('all');w=c.winfo_width();h=c.winfo_height()
    size=max(1,min((w-12)//8,(h-12)//8));ox=(w-size*8)//2;oy=(h-size*8)//2
    if size<8:return
    self.geometry=(ox,oy,size)
    events=self.entries();idx=min(self.replay_index,len(events)-1)
    event=events[idx];board=event['board']
    self.event_detail.config(text=event['label'])
    check_s=r.state_from_dict(event)
    checked={check_s.b.index('K' if side==0 else 'k') for side in (0,1) if r.in_check(check_s,side)}
    marks=event.get('squares',[])
    moves={m[1] for m in self.g.legal() if m[0]==self.selected} if self.selected is not None and not self.replay and idx==len(events)-1 else set()
    for row in range(8):
     for col in range(8):
      x=7-col if self.flip else col;y=row if self.flip else 7-row;i=r.sq(x,y)
      x0=ox+col*size;y0=oy+row*size
      fill='#e9d7b1' if (x+y)%2 else '#8c674e'
      if i in marks:fill='#bd9d66' if (x+y)%2 else '#a87a47'
      if i==self.selected:fill='#d4b35a'
      if i in checked:fill='#ce6660'
      c.create_rectangle(x0,y0,x0+size,y0+size,fill=fill,outline=fill)
      if i in moves:c.create_oval(x0+size*.41,y0+size*.41,x0+size*.59,y0+size*.59,fill='#437e77',outline='')
      p=board[i]
      if p=='H':self.axe(c,x0,y0,size)
      elif p in SYMBOL:
       pixels=min((20,28,36,44,52,60,68,76,84,96,112,128),key=lambda n:abs(n-size*.86))
       key=('w' if p.isupper() else 'b')+p.lower()+'_'+str(pixels)
       if key not in self.piece_images:self.piece_images[key]=tk.PhotoImage(file=str(ROOT/'assets'/'pieces'/(key+'.png')))
       c.create_image(x0+size*.5,y0+size*.5,image=self.piece_images[key])
      if col==0:c.create_text(x0+5,y0+7,text=str(y+1),font=('Segoe UI',max(7,int(size*.12))),fill='#253238',anchor='nw')
      if row==7:c.create_text(x0+size-5,y0+size-3,text=r.FILE[x],font=('Segoe UI',max(7,int(size*.12))),fill='#253238',anchor='se')
    c.create_rectangle(ox,oy,ox+8*size,oy+8*size,outline='#d8b975',width=3)
    self.draw_eval()
 def axe(self,c,x,y,s):
    # Vector Dane axe: broad crescent blade, socket and long haft, no font dependency.
    cx=x+s*.51
    c.create_line(cx-s*.02,y+s*.32,cx+s*.07,y+s*.82,fill='#271d19',width=max(3,s*.105),capstyle='round')
    c.create_line(cx-s*.02,y+s*.32,cx+s*.07,y+s*.82,fill='#91673e',width=max(2,s*.062),capstyle='round')
    pts=[(.31,.18),(.65,.13),(.76,.24),(.61,.36),(.43,.37),(.27,.52),(.34,.37),(.33,.29)]
    c.create_polygon(*[v for a,b in pts for v in (x+a*s,y+b*s)],fill='#e7e8da',outline='#272f32',width=max(2,s*.035),smooth=True)
    c.create_line(x+s*.29,y+s*.2,x+s*.32,y+s*.45,fill='#657579',width=max(1,s*.025),smooth=True)
 def click(self,event):
    if not self.active() or self.busy or self.paused or self.replay_index!=len(self.g.log)-1:return
    old_side=self.g.side;self.g.start_turn()
    if self.g.side!=old_side or self.g.winner:self.refresh();return
    if not hasattr(self,'geometry'):return
    ox,oy,s=self.geometry;col=(event.x-ox)//s;row=(event.y-oy)//s
    if not (0<=col<8 and 0<=row<8):return
    x=7-col if self.flip else col;y=row if self.flip else 7-row;j=r.sq(x,y)
    if self.selected is not None:
     ms=[m for m in self.g.legal() if m[0]==self.selected and m[1]==j]
     if ms:
      if len(ms)>1:
       pro=self.promotion()
       if not pro:return
       ms=[m for m in ms if m[2]==pro]
      self.g.move(ms[0]);self.selected=None;self.refresh();return
    self.selected=j if any(m[0]==j for m in self.g.legal()) else None;self.draw()
 def promotion(self):
    dialog=tk.Toplevel(self.root);dialog.title('Choose promotion');dialog.transient(self.root);dialog.grab_set()
    result=[]
    for p in 'qrbn':
     ttk.Button(dialog,text=p.upper(),command=lambda v=p:(result.append(v),dialog.destroy())).pack(side='left',padx=8,pady=10)
    self.root.wait_window(dialog)
    return result[0] if result else None
 def pump(self):
    if self.closed:return
    while True:
     try:kind,token,payload=self.worker.results.get_nowait()
     except queue.Empty:break
     if kind.startswith('simulation_'):
      if kind=='simulation_progress':self.status.config(text=payload)
      else:
       self.sim_cancel=None
       (messagebox.showerror if kind=='simulation_error' else messagebox.showinfo)('Self-play',payload)
       self.refresh()
      continue
     if kind=='replay_eval':
      rid,index,score,error=payload
      if token==self.generation and self.replay and rid==id(self.replay):
       self.replay_cache[(rid,index)]=(score,error)
       if index==self.replay_index:self.draw_eval()
      continue
     if token!=self.generation:continue
     if kind=='status':self.engine_status.set(payload)
     elif kind=='ready':self.busy=False;self.engine_status.set(payload+' — ready')
     elif kind=='error':
      self.busy=False;self.paused=True;self.engine_status.set('Engine error — game paused')
      messagebox.showerror('Computer opponent unavailable',payload+'\n\n'+('Re-extract the complete application, or select Lightweight custom and resume.' if getattr(sys,'frozen',False) else 'Use Repair engine, or select Lightweight custom and resume.')+' No fallback has been substituted.')
      self.refresh()
     elif kind=='move':
      self.busy=False;m,info=payload
      if m is not None and m in self.g.legal():
       self.g.move(m);self.g.log[-1].setdefault('engine_info',info)
       self.engine_status.set(f"{info['mode']}: {info['seconds']:.2f}s · {info['nodes']:,} nodes")
       self.refresh()
      elif not self.g.winner:
       self.paused=True;messagebox.showerror('Computer move','Invalid or missing move; game paused.');self.refresh()
    if not self.replay and not self.busy and not self.g.winner and not self.paused and not self.sim_cancel:
     if self.g.side==0:
      old=len(self.g.log);self.g.start_turn()
      if len(self.g.log)!=old:self.refresh()
     if not self.active() and not self.g.winner:
      self.busy=True
      try:level=max(1,min(10,self.level.get()))
      except (ValueError,tk.TclError):level=3;self.level.set(3)
      self.worker.submit(self.generation,self.g.clone(),self.engine_mode.get(),level,self.cancel)
      self.refresh()
    self.tick=self.root.after(100,self.pump)

if __name__=='__main__':
 if '--gui-smoke' in sys.argv:
  from packaged_smoke import run
  run()
 elif '--smoke-test' in sys.argv or '--smoke-engine' in sys.argv:
  from engine_uci import FairyEngine
  from hybrid import Hybrid
  e=FairyEngine()
  try:
   assert (ROOT/'assets'/'pieces'/'wk_68.png').is_file()
   assert (ROOT/'engine'/'hastings.ini').is_file()
   sample=Game();move=Hybrid(e,level=3,nodes=1500).choose(sample)
   assert move in sample.legal();sample.move(move)
   housecarl=r.State();housecarl.b=['.']*64
   housecarl.b[r.sq(0,0)]='K';housecarl.b[r.sq(7,7)]='k';housecarl.b[r.sq(3,3)]='H'
   housecarl.castle=dict.fromkeys('KQkq',False)
   from engine_uci import uci_move
   assert e.legal_moves(housecarl,0)=={uci_move(m) for m in r.legal(housecarl,0)}
   if '--smoke-test' in sys.argv:
    root=tk.Tk();root.withdraw();app=App(root);app.close()
  finally:e.close()
 else:
  root=tk.Tk();ttk.Style().theme_use('clam');App(root);root.mainloop()
