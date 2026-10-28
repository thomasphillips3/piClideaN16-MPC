"""Assemble the portable aarch64 (Gen2) installation archive. Reuses the ARMv7 payload, swaps the engine and manifest arch."""
from pathlib import Path
import hashlib,json,zipfile
from project_config import VERSION
B=Path(__file__).resolve().parents[1]
src=B/'Installation'/f'piClideaN-MPC-{VERSION}-armv7.zip';dest=B/'Installation'/f'piClideaN-MPC-{VERSION}-aarch64.zip'
prefix=f'piClideaN-MPC-{VERSION}/'
engine=(B/'build/aarch64/piclidean_mpc.so').read_bytes()
if engine[:5]!=b'\x7fELF\x02' or int.from_bytes(engine[18:20],'little')!=183:raise SystemExit('Not an aarch64 ELF64 engine')
payload={}
with zipfile.ZipFile(src) as z:
    for i in z.infolist():
        if i.filename.endswith('/'):continue
        payload[i.filename[len(prefix):]]=z.read(i)
for k in list(payload):
    if k.endswith('/piclidean_mpc.so'):payload[k]=engine
    elif k.endswith('mpc-plugin.json'):
        m=json.loads(payload[k]);m['arch']='aarch64';payload[k]=(json.dumps(m,ensure_ascii=False,indent=2)+'\n').encode()
payload.pop('SHA256SUMS',None)
payload['SHA256SUMS']=''.join(hashlib.sha256(d).hexdigest()+'  '+n+'\n' for n,d in sorted(payload.items())).encode()
with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
    for n,d in sorted(payload.items()):
        r=zipfile.ZipInfo(prefix+n,(2026,10,28,0,0,0));r.create_system=3
        r.external_attr=(0o100755 if n.endswith('/piclidean_mpc.so') else 0o100644)<<16;r.compress_type=zipfile.ZIP_DEFLATED;z.writestr(r,d)
with zipfile.ZipFile(dest) as z:assert not z.testzip()
dest.with_suffix(dest.suffix+'.sha256').write_text(hashlib.sha256(dest.read_bytes()).hexdigest()+'  '+dest.name+'\n')
print(dest)
