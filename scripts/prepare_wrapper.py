"""Verify the already-vendored, locally patched wrapper; never download or rewrite it."""
from pathlib import Path
import hashlib, json
B=Path(__file__).resolve().parents[1]/'third_party/mpc-vst-wrapper'
meta=json.loads((B/'VENDORED.json').read_text())
for record in meta['files']:
    expected = meta['patched_wrapper_sha256'] if record['file']=='wrapper/vst2_wrap.c' else record['sha256']
    actual = hashlib.sha256((B/record['file']).read_bytes()).hexdigest()
    if actual != expected: raise SystemExit('Vendored input changed: '+record['file']+'; review and record its provenance before building')
print('Pinned wrapper and generator inputs verified')
