"""Shared build receipts. No device access; source-only refresh never rewrites the installed ZIP."""
from pathlib import Path
import hashlib,json,datetime,os
B=Path(__file__).resolve().parents[1]
def sha(data):return hashlib.sha256(data).hexdigest()
def inputs():
    paths=[]
    for folder in ['src','scripts','third_party']:
        paths.extend(p for p in (B/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and not p.name.endswith('.pyc'))
    paths.extend(B/n for n in ['params.json','params.lock','vst.json','reference/skin-base.zip','reference/DRUMTRACK-REFERENCE.json'])
    paths.extend(p for p in (B/'reference/fonts').rglob('*') if p.is_file())
    result={}
    for p in sorted(set(paths)):
        if p.is_symlink():raise RuntimeError('Symlink build input: '+str(p))
        result[p.relative_to(B).as_posix()]=sha(p.read_bytes())
    return result

def tree(folder):
    result={}
    for p in sorted(folder.rglob('*')):
        if p.is_symlink():raise RuntimeError('Symlink generated input: '+str(p))
        if p.is_file():result[p.relative_to(folder).as_posix()]=sha(p.read_bytes())
    return result

def timestamp():
    value=os.environ.get('SOURCE_DATE_EPOCH')
    dt=datetime.datetime.fromtimestamp(int(value),datetime.timezone.utc) if value is not None else datetime.datetime.now(datetime.timezone.utc)
    return dt.isoformat(timespec='seconds')

def build_date():
    from zoneinfo import ZoneInfo
    return datetime.datetime.fromisoformat(timestamp()).astimezone(ZoneInfo("Europe/Paris")).date().isoformat()
