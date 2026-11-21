"""Actual UE5.8.4 Insights CLI exports, with retained per-export logs."""
import argparse,subprocess,json,os
from pathlib import Path
from C1Run import write,sha
def main():
    p=argparse.ArgumentParser();p.add_argument('run',type=Path);p.add_argument('--memory',action='store_true');a=p.parse_args();r=a.run.resolve()
    trace=r/'capture.utrace';assert trace.is_file();out=r/'Exports';out.mkdir(exist_ok=False)
    commands=[f'TimingInsights.ExportThreads {out.as_posix()}/threads.csv',f'TimingInsights.ExportTimers {out.as_posix()}/timers.csv',f'TimingInsights.ExportTimingEvents {out.as_posix()}/events.csv -region=U04C1_WINDOW -columns=* -timers=U04C1_*,Frame* -threads=GameThread,GPU*',f'TimingInsights.ExportTimerStatistics {out.as_posix()}/statistics.csv -region=U04C1_WINDOW',f'TimingInsights.ExportCounters {out.as_posix()}/counters.csv']
    if a.memory:
        commands=[f'MemoryInsights.ExportAllocs -Rule={rule} -BookmarkA=U04C1_START'+(' -BookmarkB=U04C1_END' if rule in ('AaB','AfB') else '')+f' -Output={out.as_posix()}/{name}.csv' for rule,name in [('AaB','allocations'),('AfB','frees'),('aAf','outstanding-start')]]
        commands.append(f'MemoryInsights.ExportAllocs -Rule=aAf -BookmarkA=U04C1_END -Output={out.as_posix()}/outstanding-end.csv')
    commandfile=out/'commands.txt';commandfile.write_text('\n'.join(commands)+'\n',encoding='utf-8')
    exe=Path('D:/Software/UE_5.8/Engine/Binaries/Win64/UnrealInsights.exe')
    command=f'"{exe}" -OpenTraceFile="{trace}" -ABSLOG="{out/"Insights.log"}" -AutoQuit -NoUI -ExecOnAnalysisCompleteCmd="@={commandfile}"'
    # Symbols from the native build and package are local; never download engine symbols.
    env=os.environ.copy();env['_NT_SYMBOL_PATH']='';env['UE_INSIGHTS_SYMBOL_PATH']=str(r.parents[1]/'Source/Binaries/Win64')
    process=subprocess.Popen(command,creationflags=subprocess.CREATE_NO_WINDOW,env=env)
    write(out/'process.json',dict(pid=process.pid,command=command,traceSHA256=sha(trace),symbolPath=env['UE_INSIGHTS_SYMBOL_PATH']))
    code=process.wait(timeout=600);write(out/'exit.json',dict(exitCode=code,exports=[dict(path=f.name,bytes=f.stat().st_size,sha256=sha(f)) for f in out.glob('*.csv')]))
    assert code==0
if __name__=='__main__':main()
