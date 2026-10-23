"""Fetch pinned official Debian compiler inputs. No sudo, system changes or device access."""
from pathlib import Path
import concurrent.futures, hashlib, json, subprocess, urllib.request
B = Path(__file__).resolve().parents[1]
records = json.loads((B/'docs/TOOLCHAIN.json').read_text())['packages']
cache = B/'downloads'; cache.mkdir(exist_ok=True)
root = B/'toolchain/root'; root.mkdir(parents=True, exist_ok=True)
def fetch(record):
    path = cache/Path(record['Filename']).name
    if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != record['SHA256']:
        url = 'https://deb.debian.org/debian/' + record['Filename']
        temporary = path.with_suffix(path.suffix+'.part')
        with urllib.request.urlopen(url, timeout=90) as response, temporary.open('wb') as output:
            while data := response.read(1024*1024): output.write(data)
        if hashlib.sha256(temporary.read_bytes()).hexdigest() != record['SHA256']:
            temporary.unlink(); raise RuntimeError('Checksum mismatch: '+path.name)
        temporary.replace(path)
    print('Verified', path.name, flush=True)
    return path
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
    paths = list(executor.map(fetch, records))
for path in paths:
    subprocess.run(['dpkg-deb','-x',str(path),str(root)],check=True)
print('Local toolchain ready:', root)
