"""Render the accepted baseline as a workload table without changing evidence."""
import argparse
import json
from pathlib import Path

from C1Run import ROOT, read, sha


def main(out):
    gate=read(ROOT/'Docs/U04/C1/GATES.json')
    entries=gate['baselineReview']['evidence']
    for e in entries.values():
        assert sha(ROOT.parent/e['path'])==e['sha256'], e['path']
    result=read(ROOT.parent/entries['comparison.json']['path'])
    out.mkdir(exist_ok=False)
    lines=[
        '# Build-03 accepted baseline',
        '',
        'Review B, one process, one Game world and one 60 s measured window after 30 s warmup.',
        'Native source `'+gate['sourceSHA']+'`. Execution tooling is recorded per run in command.json. The final continuation used `'+gate['baselineReview']['runtimeTooling']+'`.',
        '',
        'Each timing cell lists FPS and frame P50 / P95 / P99 / max in ms, in round order. Click the workload for scope, GPU, counter and memory data.',
        '',
        '| Workload | Timing round 1 | Timing round 2 | Timing round 3 | Memory allocations / frees |',
        '|---|---:|---:|---:|---:|',
    ]
    for w in result['workloads']:
        key=f"{w['subjects']}x{w['boxes']}-{w['placement']}"
        timing=sorted(w['timing'],key=lambda r:r['round'])
        assert len(timing)==3 and len(w['memory'])==1
        def cell(r):
            f=r['frameMs']
            return f"{r['fps']:.3f}; " + ' / '.join(f'{f[k]:.3f}' for k in ('p50','p95','p99','max'))
        m=w['memory'][0]['export']
        lines.append('| ['+key+']('+key+'.json) | '+' | '.join(map(cell,timing))+f" | {m['allocations']['count']:,} / {m['frees']['count']:,} |")
        (out/(key+'.json')).write_text(json.dumps(w,indent=2),encoding='utf-8')
    lines += ['', '### Metric definitions','',
        '- Native profiling wall timestamps use Windows QPC with the UE platform-time offset. FPS is the native sampled frame count divided by the native window duration. Frame distribution uses sampled dt in milliseconds.',
        '- CPU inclusive/exclusive costs are Insights region aggregates on GameThread. Per-frame divides by the exported Game Frames count and per-action divides by 60. Values in workload JSON are seconds.',
        '- GPU frame/pass sums use positive durations intersected with U04C1_WINDOW, listed by queue and timer. Nested scopes and overlapping queues can overlap in time.',
        '- Memory lifetime queries use the START/END bookmarks. Totals are counts and bytes. Whole-window attribution uses top functions. Full allocation callstacks are sampled for 50 ms.',
        '', '### Observed comparisons','',
        '- At H=3 in range, FPS changed from about 60.016 (1 target) and 60.014?60.016 (10 targets) to 59.084?59.106 (40 targets). At 40x3/in, P99 was 28.279?29.211 ms. At 40x3/out it stayed near 16.667 ms.',
        '- The comparison JSON retains subject, hurtbox and placement comparisons at matched conditions, with the three separate timing values and the median/range. Scope and GPU pass evidence stays attached to the run.',
        '- The three overhead pairs measure enabling timing trace with the existing instrumentation. No correction factor is applied.',
        '', 'Reopen and simultaneous two-world isolation have source evidence only. Occlusion and duplicate suppression remain aggregate counters.',
    ]
    (out/'BASELINE.md').write_text(chr(10).join(lines)+chr(10),encoding='utf-8')
    (out/'matched-comparisons.json').write_text(json.dumps(result['comparisons'],indent=2),encoding='utf-8')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('out',type=Path)
    main(parser.parse_args().out)
