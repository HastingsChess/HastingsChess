"""Verify/repair the pinned official engine. No pip or manual configuration."""
from pathlib import Path
import hashlib,json,os,platform,urllib.request
BASE=Path(__file__).resolve().parent

def setup(progress=print):
    machine=platform.machine().lower()
    if machine not in ('amd64','x86_64'):raise RuntimeError('Bundled Fairy-Stockfish targets Intel/AMD 64-bit Windows or Linux. Use the lightweight opponent on this architecture.')
    name='fairy-stockfish.exe' if os.name=='nt' else 'fairy-stockfish-linux'
    folder=BASE/'engine';manifest=json.loads((folder/'manifest.json').read_text())
    info=manifest['files'][name];dest=folder/name
    if dest.exists() and hashlib.sha256(dest.read_bytes()).hexdigest()==info['sha256']:
        if os.name!='nt':dest.chmod(0o755)
        progress('Official engine verified.');return dest
    progress('Downloading the pinned official Fairy-Stockfish release…')
    request=urllib.request.Request(info['url'],headers={'User-Agent':'HastingsChess/2'})
    with urllib.request.urlopen(request,timeout=60) as response:data=response.read(info['bytes']+1)
    if len(data)!=info['bytes'] or hashlib.sha256(data).hexdigest()!=info['sha256']:
        raise RuntimeError('Engine download failed integrity verification; the existing file was not replaced.')
    temp=dest.with_suffix('.download');temp.write_bytes(data);temp.replace(dest)
    if os.name!='nt':dest.chmod(0o755)
    progress('Official engine installed and verified.');return dest

if __name__=='__main__':
    try:
        setup()
        from engine_uci import FairyEngine
        engine=FairyEngine();print(engine.name+' — Hastings variant loaded.');engine.close()
    except Exception as exc:
        print('Engine setup failed:',exc);raise SystemExit(1)
