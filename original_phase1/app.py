"""Hastings Chess desktop app. Offline, standard-library Tk interface."""
import json, random, threading, time
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import rules as r
from game import Game,replay_valid
from ai import Search

ROOT=Path(__file__).resolve().parent
SYMBOL={'K':'♔','Q':'♕','R':'♖','B':'♗','N':'♘','P':'♙',
        'k':'♚','q':'♛','r':'♜','b':'♝','n':'♞','p':'♟'}

class App:
 def __init__(self,root):
    self.root=root;root.title('Hastings Chess — Random Catastrophes');root.minsize(640,580)
    self.g=Game(random.randrange(1,2**30));self.mode=tk.StringVar(value='Saxons vs computer')
    self.level=tk.IntVar(value=2);self.delay=tk.IntVar(value=350)
    self.selected=None;self.flip=False;self.replay=None;self.replay_index=0
    self.busy=False;self.generation=0;self.playing=False;self.silent=tk.BooleanVar(value=False)
    root.configure(bg='#15242b')
    bar=ttk.Frame(root,padding=8);bar.pack(fill='x')
    ttk.Button(bar,text='New battle',command=self.new).pack(side='left')
    ttk.Combobox(bar,textvariable=self.mode,values=['Saxons vs computer','Normans vs computer','Computer vs computer','Two humans'],state='readonly',width=21).pack(side='left',padx=5)
    ttk.Label(bar,text='Depth').pack(side='left');ttk.Spinbox(bar,from_=1,to=4,textvariable=self.level,width=3).pack(side='left')
    tools=ttk.Frame(root,padding=(8,0,8,5));tools.pack(fill='x')
    ttk.Button(tools,text='Flip',command=self.flip_board).pack(side='left',padx=4)
    ttk.Button(tools,text='Undo',command=self.undo).pack(side='left')
    ttk.Button(tools,text='Save',command=self.save).pack(side='left',padx=4)
    ttk.Button(tools,text='Open replay',command=self.open_replay).pack(side='left')
    ttk.Button(tools,text='Simulate',command=self.simulate).pack(side='left',padx=4)
    body=ttk.Frame(root,padding=8);body.pack(fill='both',expand=True)
    self.canvas=tk.Canvas(body,bg='#17262e',highlightthickness=0)
    self.canvas.pack(side='left',fill='both',expand=True)
    self.canvas.bind('<Configure>',lambda e:self.draw());self.canvas.bind('<Button-1>',self.click)
    panel=ttk.Frame(body,width=205);panel.pack(side='right',fill='y',padx=(8,0));panel.pack_propagate(False)
    self.status=ttk.Label(panel,text='',wraplength=215,justify='left',font=('Segoe UI',11,'bold'));self.status.pack(anchor='w',pady=(0,12))
    self.odds=ttk.Label(panel,text='',wraplength=215,justify='left');self.odds.pack(anchor='w')
    self.knights=ttk.Label(panel,text='');self.knights.pack(anchor='w',pady=6)
    ttk.Label(panel,text='The chronicle',font=('Segoe UI',10,'bold')).pack(anchor='w',pady=(10,2))
    self.events=tk.Listbox(panel,selectmode='browse',font=('Segoe UI',9),exportselection=False)
    self.events.pack(fill='both',expand=True);self.events.bind('<<ListboxSelect>>',self.select_event)
    rep=ttk.Frame(panel);rep.pack(fill='x',pady=5)
    for caption,fun in [('◀',self.previous),('▶',self.next),('Charge',self.jump_charge),('Live',self.live)]:
        ttk.Button(rep,text=caption,command=fun,width=6).pack(side='left',expand=True)
    ttk.Label(panel,text='Replay: select an event. Bonus actions have their own entries.',wraplength=205).pack(anchor='w')
    self.refresh();root.after(200,self.pump)

 def new(self):
    self.generation+=1;self.g=Game(random.randrange(1,2**30));self.replay=None
    self.selected=None;self.busy=False;self.playing=False;self.refresh()
 def flip_board(self):self.flip=not self.flip;self.draw()
 def undo(self):
    self.generation+=1;self.busy=False;self.replay=None
    if self.g.undo():self.refresh()
 def save(self):
    p=filedialog.asksaveasfilename(defaultextension='.json',filetypes=[('Hastings replay','*.json')])
    if p:Path(p).write_text(json.dumps(self.g.export(),indent=2),encoding='utf-8')
 def open_replay(self):
    p=filedialog.askopenfilename(filetypes=[('Hastings replay','*.json')])
    if not p:return
    try:self.replay=replay_valid(json.loads(Path(p).read_text(encoding='utf-8')))
    except (OSError,ValueError,KeyError,TypeError) as e:messagebox.showerror('Replay error',str(e));return
    self.generation+=1;self.busy=False;self.replay_index=0;self.refresh()
 def simulate(self):
    from simulate import run
    count=simpledialog.askinteger('Self-play','Games (1–1000):',initialvalue=20,minvalue=1,maxvalue=1000,parent=self.root)
    if count is None:return
    path=filedialog.asksaveasfilename(defaultextension='.json',filetypes=[('JSON statistics and replays','*.json')])
    if not path:return
    seed=random.randrange(1,2**30)
    self.status.config(text=f'Simulating {count} games in the background…')
    def work():
     try:
      data=run(count,seed,60,min(self.level.get(),2),.08)
      Path(path).write_text(json.dumps(data,indent=2),encoding='utf-8')
      msg=f'{count} games saved. Outcomes: '+', '.join(f'{k} {v}' for k,v in data['outcomes'].items())
      self.root.after(0,lambda:messagebox.showinfo('Simulation complete',msg))
     except Exception as e:self.root.after(0,lambda err=str(e):messagebox.showerror('Simulation error',err))
     self.root.after(0,self.refresh)
    threading.Thread(target=work,daemon=True).start()
 def entries(self):return self.replay['events'] if self.replay else self.g.log
 def previous(self):self.replay_index=max(0,self.replay_index-1);self.draw()
 def next(self):self.replay_index=min(len(self.entries())-1,self.replay_index+1);self.draw()
 def jump_charge(self):
    for i,e in enumerate(self.entries()):
        if e['phase']=='charge':self.replay_index=i;self.draw();return
 def live(self):
    if not self.replay:self.replay_index=len(self.g.log)-1;self.draw()
 def select_event(self,event):
    v=self.events.curselection()
    if v:self.replay_index=v[0];self.draw()
 def active(self):
    if self.replay or self.g.winner:return False
    mode=self.mode.get()
    return mode=='Two humans' or (mode=='Saxons vs computer' and self.g.side==0) or (mode=='Normans vs computer' and self.g.side==1)
 def refresh(self):
    e=self.entries();self.events.delete(0,'end')
    for event in e:self.events.insert('end',event['label'])
    self.replay_index=len(e)-1
    self.events.selection_set(self.replay_index);self.events.see(self.replay_index)
    status=('Replay' if self.replay else f'{"Saxons" if self.g.side==0 else "Normans"} to act — {self.g.phase}')
    if self.g.winner:status=f'{self.g.winner.title()} — {self.g.reason}'
    self.status.config(text=status)
    self.odds.config(text=f'White move {self.g.white_move}: charge chance {self.g.odds():.0%} (conditional)' if not self.replay else 'Saved battle')
    self.knights.config(text=f'Norman knights surviving: {self.g.s.b.count("n")}')
    self.draw()
 def draw(self):
    c=self.canvas;c.delete('all');w=c.winfo_width();h=c.winfo_height()
    size=max(1,min((w-12)//8,(h-12)//8));ox=(w-size*8)//2;oy=(h-size*8)//2
    if size<8:return
    self.geometry=(ox,oy,size)
    events=self.entries();idx=min(self.replay_index,len(events)-1)
    event=events[idx];board=event['board']
    marks=event.get('squares',[])
    moves={m[1] for m in self.g.legal() if m[0]==self.selected} if self.selected is not None and not self.replay and idx==len(events)-1 else set()
    for row in range(8):
     for col in range(8):
      x=7-col if self.flip else col;y=row if self.flip else 7-row;i=r.sq(x,y)
      x0=ox+col*size;y0=oy+row*size
      fill='#e9d7b1' if (x+y)%2 else '#8c674e'
      if i in marks:fill='#bd9d66' if (x+y)%2 else '#a87a47'
      if i==self.selected:fill='#d4b35a'
      c.create_rectangle(x0,y0,x0+size,y0+size,fill=fill,outline=fill)
      if i in moves:c.create_oval(x0+size*.41,y0+size*.41,x0+size*.59,y0+size*.59,fill='#437e77',outline='')
      p=board[i]
      if p=='H':self.axe(c,x0,y0,size)
      elif p in SYMBOL:
       c.create_text(x0+size*.5+1,y0+size*.51+2,text=SYMBOL[p],font=('Segoe UI Symbol',int(size*.68)),fill='#332a24')
       c.create_text(x0+size*.5,y0+size*.49,text=SYMBOL[p],font=('Segoe UI Symbol',int(size*.68)),fill='#fff9e8' if p.isupper() else '#192228')
      if col==0:c.create_text(x0+5,y0+7,text=str(y+1),font=('Segoe UI',max(7,int(size*.12))),fill='#253238',anchor='nw')
      if row==7:c.create_text(x0+size-5,y0+size-3,text=r.FILE[x],font=('Segoe UI',max(7,int(size*.12))),fill='#253238',anchor='se')
    c.create_rectangle(ox,oy,ox+8*size,oy+8*size,outline='#d8b975',width=3)
 def axe(self,c,x,y,s):
    # Vector Dane axe: broad crescent blade, socket and long haft, no font dependency.
    cx=x+s*.51
    c.create_line(cx-s*.02,y+s*.32,cx+s*.07,y+s*.82,fill='#271d19',width=max(3,s*.105),capstyle='round')
    c.create_line(cx-s*.02,y+s*.32,cx+s*.07,y+s*.82,fill='#91673e',width=max(2,s*.062),capstyle='round')
    pts=[(.31,.18),(.65,.13),(.76,.24),(.61,.36),(.43,.37),(.27,.52),(.34,.37),(.33,.29)]
    c.create_polygon(*[v for a,b in pts for v in (x+a*s,y+b*s)],fill='#e7e8da',outline='#272f32',width=max(2,s*.035),smooth=True)
    c.create_line(x+s*.29,y+s*.2,x+s*.32,y+s*.45,fill='#657579',width=max(1,s*.025),smooth=True)
 def click(self,event):
    if not self.active() or self.busy:return
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
    if not self.replay and not self.busy and not self.g.winner:
     if self.g.side==0:
      old=len(self.g.log);self.g.start_turn()
      if len(self.g.log)!=old:self.refresh()
     if not self.active() and not self.g.winner and not self.busy:
      self.busy=True;generation=self.generation;game=self.g
      level=self.level.get()
      def work():
       try:m=Search(level,min(3,.25+.45*level)).choose(game)
       except Exception as e:m=e
       def done():
        if generation!=self.generation:return
        self.busy=False
        if isinstance(m,Exception):messagebox.showerror('Computer move',str(m));return
        if m and m in self.g.legal():self.g.move(m);self.refresh()
       self.root.after(0,done)
      threading.Thread(target=work,daemon=True).start()
    self.root.after(max(100,self.delay.get()),self.pump)

if __name__=='__main__':
 root=tk.Tk();ttk.Style().theme_use('clam');App(root);root.mainloop()
