"""Read-only trace correlation around real Windows Dodge inputs on two clients."""
import argparse,ctypes,json,time,traceback
from pathlib import Path
from NetworkClientB import NetworkClientB,u,Input,Payload,Key,VK

def main():
    p=argparse.ArgumentParser();p.add_argument('--session',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    records=json.loads((a.session/'processes.json').read_text(encoding='utf-8-sig'));server=next(r for r in records if r['role']=='Server')
    report=dict(completed=False,acceptance=False,purpose='NETWORK_DIRECTION_REGRESSION',processes=records,trials=[])
    def until(f,seconds=8):
        end=time.perf_counter()+seconds
        while not f():
            assert time.perf_counter()<end,'network condition timeout';time.sleep(.05)
    def traces(record,offset=0):
        with Path(record['log']).open('rb') as f:f.seek(offset);data=f.read()
        data=data[:data.rfind(b'\n')+1].decode('utf-8-sig')
        return [json.loads(l.split('U04R1_INPUT ',1)[1]) for l in data.splitlines() if 'U04R1_INPUT {' in l]
    def button(c,label):
        until(lambda:label in c.metrics()['menuButtons'] and c.metrics()['menuButtons'][label]['enabled'])
        b=c.metrics()['menuButtons'][label];c.click(round(b['x']),round(b['y']));time.sleep(.25)
    try:
        for role in ('ClientA','ClientB'):
            record=next(r for r in records if r['role']==role);c=NetworkClientB(record)
            try:
                c.focus();seen=c.probe_w()
                if seen!='W':c.toggle_ime();c.ime=True;seen=c.probe_w()
                assert seen=='W'
                if c.metrics()['combat']['vital']['hp']<1000 and not c.metrics()['encounter']['result']:until(lambda:c.metrics()['encounter']['result']!=0,22)
                if c.metrics()['encounter']['result']:
                    revision=c.metrics()['encounter']['revision'];button(c,'Retry encounter');until(lambda:c.metrics()['encounter']['revision']>revision)
                if c.metrics()['controlState']!=0:button(c,'Resume')
                until(lambda:c.metrics()['controlState']==0)
                before=c.metrics();offsets={r['role']:Path(r['log']).stat().st_size for r in records}
                c.guard();batch=(Input*2)(Input(type=1,payload=Payload(key=Key(vk=VK['W']))),Input(type=1,payload=Payload(key=Key(vk=0,scan=0x2a,flags=8))))
                start=time.perf_counter();count=u.SendInput(2,batch,ctypes.sizeof(Input));stop=time.perf_counter();assert count==2;c.held.update({'W','Shift'})
                time.sleep(.1);c.press('Shift',False);c.press('W',False);time.sleep(.7)
                client_rows=traces(record,offsets[role]);sent=[r for r in client_rows if r['event']=='Sent'];assert len(sent)==1
                s=sent[0];key=lambda r:(r['pawn'],r['life'],r['command'])
                server_rows=traces(server,offsets['Server']);received=[r for r in server_rows if r['event']=='Received' and key(r)==key(s)]
                admissions=[r for r in server_rows if r['event']=='AuthorityAdmission' and key(r)==key(s)]
                trial=dict(role=role,before=before,processIdentity=c.processIdentity,windowsBatch=[['W',True],['Shift',True]],qpcBefore=start,qpcAfter=stop,
                           clientTrace=client_rows,serverTrace=server_rows,sent=s,received=received,admissions=admissions,status='FAIL')
                report['trials'].append(trial)
                assert [s['x'],s['y']]==[1,0] and not s['authority'],'client snapshot'
                assert len(received)==1 and received[0]['authority'] and [received[0]['x'],received[0]['y']]==[s['x'],s['y']],'server transport'
                assert len(admissions)==1 and admissions[0]['authority'] and admissions[0]['admission']==0,'server admission'
                assert not any(r['event']=='AuthorityAdmission' for r in client_rows),'client must not admit'
                trial['status']='PASS'
                if c.metrics()['controlState']==0:c.press('Escape',True);time.sleep(.04);c.press('Escape',False)
            finally:c.finish()
        assert len({r['sent']['pawn'] for r in report['trials']})==2
        report['completed']=True
    except Exception as error:report.update(error=repr(error),traceback=traceback.format_exc());raise
    finally:(a.out/'direction-network.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('PASS two-client direction transport and server admission')

if __name__=='__main__':main()
