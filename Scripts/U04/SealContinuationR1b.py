"""Publish R1b continuation evidence without changing frozen tools or claiming readiness."""
import argparse,gzip,hashlib,json,re,shutil,subprocess
from datetime import datetime,timezone
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--isolation',required=True,type=Path);p.add_argument('--publish',required=True,type=Path);p.add_argument('--gates',required=True,type=Path);a=p.parse_args()
root=Path(__file__).resolve().parents[2];isolation=a.isolation.resolve();publish=a.publish.resolve()
assert publish.is_relative_to(root/'Docs/U04/R1b/Continuation/Evidence') and not publish.exists()
gates=json.loads(a.gates.read_text(encoding='utf-8'));assert gates['status'] in ('INCOMPLETE','READY_FOR_REVIEW')
publish.mkdir(parents=True);records=[]
def sha(f):
    h=hashlib.sha256()
    with f.open('rb') as s:
        for chunk in iter(lambda:s.read(8388608),b''):h.update(chunk)
    return h.hexdigest()
for f in sorted((isolation/'Runs').rglob('*')):
    if not f.is_file():continue
    rel=f.relative_to(isolation/'Runs')
    if 'Archive' in rel.parts or any(part in ('User','Settings') for part in rel.parts):continue
    dest=publish/'Runs'/rel;dest.parent.mkdir(exist_ok=True,parents=True);transform='identity'
    if f.suffix.lower() in ('.mp4','.png','.wav'):
        assert f.stat().st_size<95*1024*1024,('media too large',f);shutil.copyfile(f,dest)
    else:
        data=f.read_bytes();enc='utf-16' if data[:2] in (b'\xff\xfe',b'\xfe\xff') else 'utf-8-sig'
        try:
            text=data.decode(enc);clean=re.sub(r'(?i)(SecurityToken\s*[=:]\s*|(?:AUTH_PASSWORD|AUTH_LOGIN|epicusername|epicuserid|epicsandboxid)=)([^\s";]+)',r'\1[REDACTED]',text)
            clean=re.sub(r'(?i)("(?:SecurityToken|AUTH_PASSWORD|AUTH_LOGIN|epicusername|epicuserid)"\s*:\s*")[^"]*',r'\1[REDACTED]',clean)
            if clean!=text:data=clean.encode(enc);transform='redact-secrets'
        except UnicodeDecodeError:pass
        dest=dest.with_name(dest.name+'.gz');dest.write_bytes(gzip.compress(data,compresslevel=6,mtime=0));transform+=';gzip'
    records.append(dict(raw=rel.as_posix(),rawSHA256=sha(f),rawBytes=f.stat().st_size,published=dest.relative_to(root).as_posix(),publishedSHA256=sha(dest),publishedBytes=dest.stat().st_size,transformation=transform))
m=dict(schema=1,status=gates['status'],createdUTC=datetime.now(timezone.utc).isoformat(),rawRoot=str(isolation/'Runs'),
       gatesRawPath=str(a.gates.resolve()),gatesRawSHA256=sha(a.gates),
       sourceSHA=gates['sourceSHA'],acceptance=False,continuationBase='e1ba0d6cc2d1d8c6acdc4f329c82c68eba5e4b24',inheritance={k:gates[k] for k in ('oldManifestSHA256','oldHaltedLedgerSHA256','oldEvidenceManifestSHA256')},mainBaseline='18804bfa32b14471df1ffa4bd7aeaed6cd80074c',gates=gates,files=records,
       publisherCommit=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip(),
       warnings=['Game-thread rendered frame sampling is not scanout measurement.','Video30FPS does not establish game120FPS.','Combined69 trials include exactly23 immutable R1b30 PASS plus46 continuation trials. Old batch stays halted. Twenty-one separate illustrative videos never establish simultaneous numeric results.','No acceptance, merge, U04-C/D, adverse network or packaged Server claim.'])
f=publish/'MANIFEST.json';f.write_text(json.dumps(m,indent=2),encoding='utf-8');print(f,sha(f))
