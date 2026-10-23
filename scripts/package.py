"""Assemble the portable ARMv7 installation archive from current build outputs."""
from pathlib import Path
import hashlib,json,struct,zipfile,xml.etree.ElementTree as ET,os,tempfile
from project_config import VERSION,DISPLAY_NAME,FOLDER,SKIN_IDENTIFIER
from provenance import inputs,tree,timestamp
B=Path(__file__).resolve().parents[1]
def digest(data):return hashlib.sha256(data).hexdigest()
def main():
    build=json.loads((B/'build/reports/BUILD.json').read_text())
    if build['version']!=VERSION or build['input_hashes']!=inputs():
        raise SystemExit('Build inputs differ; run scripts/build.py first')
    skin=B/'build/skin'/FOLDER
    if build['skin_output_hashes']!=tree(skin):raise SystemExit('Skin outputs differ; rebuild first')
    engine=(B/'build/piclidean_mpc.so').read_bytes()
    if engine[:5]!=b'\x7fELF\x01' or int.from_bytes(engine[18:20],'little')!=40 or digest(engine)!=build['engine_sha256']:
        raise SystemExit('Invalid ARMv7 engine or build checksum')
    manifest=dict(schema=1,id='piclidean-mpc',name=DISPLAY_NAME,version=VERSION,distribution_revision='release',uid='5069434e',manufacturer='Timo',so='piclidean_mpc.so',skin=FOLDER,folder='portable/'+FOLDER,arch='armv7',kind='instrument',layout='portable',extras=[],user_data=[],requires='')
    metadata=ET.Element('PLUGIN',name=DISPLAY_NAME,descriptiveName=DISPLAY_NAME,format='VST',category='Synth',manufacturer='Timo',version=VERSION,file='%payload-path%/'+FOLDER+'/piclidean_mpc.so',uid='5069434e',isInstrument='1',fileTime='0',infoUpdateTime='0',numInputs='0',numOutputs='2',isShell='0')
    (B/'mpc-plugin.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    (B/'plugin-meta.xml').write_text(ET.tostring(metadata,encoding='unicode')+'\n')
    port='portable/'+FOLDER+'/'
    payload={}
    for p in skin.rglob('*'):
        if p.is_symlink():raise RuntimeError('Symbolic link in generated skin')
        if p.is_file():payload[port+p.relative_to(skin).as_posix()]=p.read_bytes()
    payload[port+'piclidean_mpc.so']=engine
    payload['mpc-plugin.json']=(B/'mpc-plugin.json').read_bytes()
    payload[port+'mpc-plugin.json']=payload['mpc-plugin.json']
    payload[port+'plugin-meta.xml']=(B/'plugin-meta.xml').read_bytes()
    payload['MODES']=b'x\tpiclidean_mpc.so\n'
    package(B,payload)
def package(base,payload):
    """Keep runtime files intact and attach only public documentation and licenses."""
    payload=dict(payload)
    for name in ['README.md','LICENSE','THIRD_PARTY.md','Cover.JPG']:payload[name]=(base/name).read_bytes()
    for folder in ['docs','licenses']:
        for p in (base/folder).rglob('*'):
            if p.is_file() and p.name not in ('TOOLCHAIN.json','piclidean-banner.png'):payload[p.relative_to(base).as_posix()]=p.read_bytes()
    payload['licenses/MPC-VST-LICENSE']=(base/'third_party/mpc-vst-wrapper/LICENSE').read_bytes()
    payload['licenses/FONT-OFL.txt']=(base/'reference/fonts/OFL.txt').read_bytes()
    payload['SHA256SUMS']=''.join(digest(data)+'  '+name+'\n' for name,data in sorted(payload.items())).encode()
    prefix='piClideaN-MPC-'+VERSION
    dest=base/'Installation'/(prefix+'-armv7.zip');dest.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=dest.parent,suffix='.partial',delete=False) as f:temp=Path(f.name)
    try:
        with zipfile.ZipFile(temp,'w',zipfile.ZIP_DEFLATED) as z:
            for name,data in sorted(payload.items()):
                if '..' in Path(name).parts or name.startswith('/') or '\\' in name:raise RuntimeError('Invalid package path')
                row=zipfile.ZipInfo(prefix+'/'+name,(2026,10,23,0,0,0));row.create_system=3
                row.external_attr=(0o100755 if name.endswith('/piclidean_mpc.so') else 0o100644)<<16;row.compress_type=zipfile.ZIP_DEFLATED
                z.writestr(row,data)
        with zipfile.ZipFile(temp) as z:
            if z.testzip():raise RuntimeError('ZIP CRC mismatch')
            for name,data in payload.items():
                if z.read(prefix+'/'+name)!=data:raise RuntimeError('ZIP content mismatch')
        os.replace(temp,dest)
    finally:
        if temp.exists():temp.unlink()
    dest.with_suffix(dest.suffix+'.sha256').write_text(digest(dest.read_bytes())+'  '+dest.name+'\n')
    print(dest)
if __name__=='__main__':main()
