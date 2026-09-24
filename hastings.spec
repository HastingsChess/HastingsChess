# Native PyInstaller build: run on the target OS, from this source directory.
import os
from pathlib import Path
from engine_uci import engine_filename

root=Path(SPECPATH)
exe=root/'engine'/engine_filename()
if not exe.is_file():raise FileNotFoundError('Engine for this platform is missing: '+str(exe))
datas=[(str(root/'assets'),'assets'),(str(root/'engine'/'hastings.ini'),'engine'),
       (str(root/'engine'/'COPYING.txt'),'engine'),
       (str(root/'engine'/'Fairy-Stockfish-fairy_sf_14.tar.gz'),'engine')]
a=Analysis([str(root/'app.py')],pathex=[str(root)],binaries=[(str(exe),'engine')],
           datas=datas,hiddenimports=[],hookspath=[],runtime_hooks=[str(root/'runtime_diagnostics.py')],excludes=[],noarchive=False)
pyz=PYZ(a.pure)
exe=EXE(pyz,a.scripts,[],exclude_binaries=True,name='HastingsChess',
        debug=False,bootloader_ignore_signals=False,strip=False,upx=False,console=False)
coll=COLLECT(exe,a.binaries,a.datas,strip=False,upx=False,name='HastingsChess')
if os.sys.platform=='darwin':
    app=BUNDLE(coll,name='Hastings Chess.app',bundle_identifier='org.hastingschess.desktop')
