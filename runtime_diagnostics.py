"""PyInstaller runtime hook: record launch failures in writable per-user data."""
import os,platform,sys,traceback
from pathlib import Path

_previous_hook=sys.excepthook

def _error_path():
    if sys.platform=='win32':
        base=Path(os.environ.get('APPDATA') or Path.home()/'AppData'/'Roaming')
        return base/'Hastings Chess'/'launch-errors.log'
    if sys.platform=='darwin':return Path.home()/'Library'/'Application Support'/'Hastings Chess'/'launch-errors.log'
    base=Path(os.environ.get('XDG_DATA_HOME') or Path.home()/'.local'/'share')
    return base/'Hastings Chess'/'launch-errors.log'

def _report_error(exc_type,exc_value,exc_tb):
    try:
        root=Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parent))
        engine_name=('fairy-stockfish.exe' if sys.platform=='win32' else
                     'fairy-stockfish-macos-'+platform.machine().lower() if sys.platform=='darwin' else
                     'fairy-stockfish-linux')
        engine=root/'engine'/engine_name;variant=root/'engine'/'hastings.ini'
        report=(f'\nHastings Chess Phase 4 | {platform.platform()} | {platform.machine()}\n'
                f'Frozen: {bool(getattr(sys,"frozen",False))}\n'
                f'Resource root: {root}\n'
                f'Engine: {engine} | exists={engine.is_file()} | executable={os.access(engine,os.X_OK)}\n'
                f'Variant: {variant} | exists={variant.is_file()}\n'
                +''.join(traceback.format_exception(exc_type,exc_value,exc_tb)))
        path=_error_path();path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('a',encoding='utf-8') as f:f.write(report)
    except Exception:pass
    _previous_hook(exc_type,exc_value,exc_tb)

sys.excepthook=_report_error
