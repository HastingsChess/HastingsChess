"""Visible GUI smoke for native packaged applications, with isolated settings."""
import os,tempfile,time,types
from pathlib import Path
import tkinter as tk
from tkinter import ttk
from settings import Settings,SAXON_RATING

def run():
    # Import here so the normal user-facing start path stays unchanged.
    from app import App
    with tempfile.TemporaryDirectory(prefix='Hastings GUI smoke ') as temp:
        root=tk.Tk();ttk.Style().theme_use('clam');root.geometry('1100x800')
        app=App(root)
        try:
            app.settings=Settings(Path(temp)/'settings.json')
            app.refresh()
            root.update()
            assert root.winfo_viewable(), 'Packaged GUI did not map a visible window'
            assert root.title()=='Hastings Chess: Catastrophic Military Stupidity Simulator. Also Axes'
            assert app.canvas.winfo_width()>200 and app.canvas.winfo_height()>200
            assert app.eval_canvas is None, 'Evaluation bar leaked into live game'
            assert app.settings.norman_elo==1066 and SAXON_RATING==1066
            assert 'Normans — Elo 1066' in app.ratings.cget('text')
            app.rules_button.invoke();root.update()
            assert app.rules_window.winfo_viewable(),'Bundled Rules window did not open'
            assert 'and it was Wednesday.' in (Path(__file__).resolve().parent/'IN_GAME_RULES.md').read_text(encoding='utf-8')
            app.rules_window.destroy();app.show_rules();root.update()
            assert app.rules_window.winfo_viewable(),'Rules window did not reopen'
            assert len(app.level_box['values'])==10
            for level in (1,3,4,10):
                app.level_text.set(app.difficulty_label(level));app.difficulty_changed()
                assert app.level.get()==level
            app.level_text.set(app.difficulty_label(1));app.difficulty_changed()
            app.new()
            ox,oy,s=app.geometry
            for square in ('e2','e4'):
                x=ord(square[0])-97;y=int(square[1])-1
                app.click(types.SimpleNamespace(x=int(ox+(x+.5)*s),y=int(oy+(7-y+.5)*s)))
            assert app.g.s.b[28]=='P','Human GUI move did not apply'
            until=time.monotonic()+15
            while time.monotonic()<until and not (app.g.side==0 and app.g.white_move==2):
                root.update();time.sleep(.02)
            assert app.g.side==0 and app.g.white_move==2,'Bundled Fairy opponent did not respond'
            assert app.eval_canvas is None,'Evaluation bar visible during live play'
            app.g._end('black','checkmate');app.refresh()
            assert app.settings.norman_elo>1066
            assert Settings(app.settings.path).norman_elo==app.settings.norman_elo
            assert 'Saxons — Elo 1066' in app.ratings.cget('text')
            assert app.eval_canvas is None,'Evaluation bar visible before Replay'
            app.review_finished();root.update()
            assert app.eval_canvas is not None,'Replay evaluation bar absent'
            assert app.eval_canvas.winfo_viewable(),'Replay evaluation bar did not map'
            app.previous();root.update()
            until=time.monotonic()+15
            while time.monotonic()<until and 'Analysing' in app.eval_label.cget('text'):
                root.update();time.sleep(.02)
            assert 'Analysing' not in app.eval_label.cget('text'),'Replay analysis did not finish'
            app.live();root.update()
            assert app.eval_canvas is None,'Replay bar leaked back into live view'
        finally:app.close()
    marker=os.environ.get('HASTINGS_SMOKE_MARKER')
    if marker:Path(marker).write_text('gui-ok\n',encoding='utf-8')
