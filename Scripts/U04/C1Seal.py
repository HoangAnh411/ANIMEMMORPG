"""Publish incomplete C1 evidence with reversible gzip and explicit redaction hashes."""
import gzip,hashlib,json,re,subprocess
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[2];ISOLATION=ROOT.parent
def sha(f):
    h=hashlib.sha256()
    with f.open('rb') as s:
        for b in iter(lambda:s.read(8388608),b''):h.update(b)
    return h.hexdigest()
def main():
    dest=ROOT/'Docs/U04/C1/Evidence';assert not dest.exists();dest.mkdir(parents=True)
    records=[]
    for f in sorted((ISOLATION/'Runs').rglob('*')):
        if not f.is_file():continue
        rel=f.relative_to(ISOLATION/'Runs')
        if any(x in ('Archive','User','Settings') for x in rel.parts):continue
        data=f.read_bytes();transform='identity'
        if f.suffix.lower() not in ('.utrace','.ucache','.uba','.pdb','.dll','.exe'):
            enc='utf-16' if data[:2] in (b'\xff\xfe',b'\xfe\xff') else 'utf-8-sig'
            try:
                text=data.decode(enc)
                clean=re.sub(r'(?i)(SecurityToken\s*[=:]\s*|(?:AUTH_PASSWORD|AUTH_LOGIN|epicusername|epicuserid|epicsandboxid)=)([^\s";]+)',r'\1[REDACTED]',text)
                clean=re.sub(r'(?i)("(?:SecurityToken|AUTH_PASSWORD|AUTH_LOGIN|epicusername|epicuserid)"\s*:\s*")[^"]*',r'\1[REDACTED]',clean)
                if clean!=text:data=clean.encode(enc);transform='redact-secrets'
            except UnicodeDecodeError:pass
        out=dest/'Runs'/rel;out=out.with_name(out.name+'.gz');out.parent.mkdir(parents=True,exist_ok=True)
        out.write_bytes(gzip.compress(data,compresslevel=6,mtime=0))
        assert out.stat().st_size<95*1024*1024
        assert gzip.decompress(out.read_bytes())==data
        records.append(dict(raw=rel.as_posix(),rawSHA256=sha(f),rawBytes=f.stat().st_size,published=out.relative_to(ROOT).as_posix(),publishedSHA256=sha(out),publishedBytes=out.stat().st_size,transformation=transform+';gzip'))
    gates=json.loads((ROOT/'Docs/U04/C1/GATES.json').read_text())
    m=dict(schema=1,status='INCOMPLETE',utc=datetime.now(timezone.utc).isoformat(),mainBaseline=gates['mainBaseline'],sourceSHA=gates['sourceSHA'],publisherCommit=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip(),rawRoot=str(ISOLATION/'Runs'),gates=gates,files=records,excluded=['Archive package binaries and PDB: retained locally, indexed in BUILD-IDENTITY and symbols.json','User/Settings: private local process data'],baselineTimingRuns=0,baselineMemoryRuns=0)
    (dest/'MANIFEST.json').write_text(json.dumps(m,indent=2),encoding='utf-8')
    print(json.dumps(dict(files=len(records),publishedBytes=sum(x['publishedBytes'] for x in records),allGzipRoundTripsVerified=True),indent=2))
if __name__=='__main__':main()
