"""Small local side ratings and UI preferences; never used by simulations."""
import json, os, sys, tempfile
from pathlib import Path

SAXON_RATING = 1066
NORMAN_INITIAL = 1066
SETTINGS_SCHEMA = 2
K_FACTOR = 32

def settings_path():
    if sys.platform == 'win32':
        root = Path(os.environ.get('APPDATA') or Path.home()/'AppData'/'Roaming')
        return root/'Hastings Chess'/'settings.json'
    if sys.platform == 'darwin':
        return Path.home()/'Library'/'Application Support'/'Hastings Chess'/'settings.json'
    return Path(os.environ.get('XDG_DATA_HOME') or Path.home()/'.local'/'share')/'Hastings Chess'/'settings.json'

def norman_next(current, result):
    if result not in (0, .5, 1):raise ValueError('Result must be 0, 0.5, or 1')
    expected = 1 / (1 + 10 ** ((SAXON_RATING - current) / 400))
    return int((current + K_FACTOR * (result - expected)) + .5)

class Settings:
    def __init__(self, path=None):
        self.path = Path(path) if path else settings_path()
        self.data = {'schema_version':SETTINGS_SCHEMA,'norman_elo':NORMAN_INITIAL,'difficulty':3,'rated_games':[]}
        try:
            source=json.loads(self.path.read_text(encoding='utf-8'))
            if isinstance(source,dict):
                n=source.get('norman_elo');level=source.get('difficulty');ids=source.get('rated_games')
                if source.get('schema_version') == SETTINGS_SCHEMA and type(n) is int and 100<=n<=4000:
                    self.data['norman_elo']=n
                if type(level) is int and 1<=level<=10:self.data['difficulty']=level
                if source.get('schema_version') == SETTINGS_SCHEMA and isinstance(ids,list):
                    self.data['rated_games']=[x for x in ids[-1000:] if isinstance(x,str)]
                if source.get('schema_version') != SETTINGS_SCHEMA:
                    self.save()  # one-time migration; subsequent rated results persist normally
        except (OSError,ValueError,TypeError):pass

    @property
    def norman_elo(self):return self.data['norman_elo']

    def save(self):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        fd,name=tempfile.mkstemp(prefix='settings-',suffix='.json',dir=self.path.parent)
        try:
            with os.fdopen(fd,'w',encoding='utf-8') as output:
                json.dump(self.data,output,indent=2)
            os.replace(name,self.path)
        finally:
            if os.path.exists(name):os.unlink(name)

    def set_difficulty(self,level):
        if not 1<=int(level)<=10:raise ValueError('Difficulty must be 1–10')
        self.data['difficulty']=int(level);self.save()

    def record(self,game_id,winner):
        """Call only for a completed rated UI game. Idempotent across restarts."""
        if winner not in ('white','black','draw'):raise ValueError('Incomplete result')
        if game_id in self.data['rated_games']:return None
        before=self.norman_elo
        after=norman_next(before,{'white':0,'draw':.5,'black':1}[winner])
        previous=self.data.copy()
        self.data['norman_elo']=after;self.data['rated_games']=(self.data['rated_games']+[game_id])[-1000:]
        try:self.save()
        except OSError:self.data=previous;raise
        return before,after
