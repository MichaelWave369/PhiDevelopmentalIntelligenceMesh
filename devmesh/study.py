"""Multiple-seed, independent evaluation across a fixed pre-specified curriculum."""
from __future__ import annotations

import html
import json
import statistics
from pathlib import Path

from .benchmark import run_benchmark


def _summarize(values: list[float]) -> dict:
    return {'mean':round(statistics.mean(values),5),
            'sample_std':round(statistics.stdev(values),5) if len(values)>1 else 0.0,
            'minimum':round(min(values),5),'maximum':round(max(values),5)}


def run_study(*, start_seed: int=369, runs: int=10, samples: int=60,
              capacity: int=9, output=None) -> dict:
    if not (2 <= runs <= 100):
        raise ValueError('runs must be between 2 and 100')
    if not (10 <= samples <= 10000):
        raise ValueError('samples must be between 10 and 10000')
    if capacity < 1:
        raise ValueError('capacity must be positive')
    individual=[]
    for seed in range(start_seed,start_seed+runs):
        trial=run_benchmark(seed=seed,samples=samples,capacity=capacity)
        first,second,third,revisit=trial['phases']
        row={'seed':seed,'models':{}}
        for model in trial['models']:
            def score(phase,world,key):
                return phase['models'][model]['scores'][world][key]
            row['models'][model]={
                'first_world_nll_start':score(first,'first_world','nll'),
                'first_world_nll_after_interference':score(third,'first_world','nll'),
                'first_world_nll_after_revisit':score(revisit,'first_world','nll'),
                'forgetting_delta_nll':round(score(third,'first_world','nll')-score(first,'first_world','nll'),5),
                'relearning_delta_nll':round(score(third,'first_world','nll')-score(revisit,'first_world','nll'),5),
                'new_world_accuracy':round((score(second,'second_world','accuracy')+score(third,'third_world','accuracy'))/2,5),
                'attempted_updates':third['models'][model]['metrics']['step'],
                'replay_steps':third['models'][model]['metrics']['replayed'],
            }
        individual.append(row)
    names=trial['models']
    keys=('forgetting_delta_nll','relearning_delta_nll','new_world_accuracy',
          'first_world_nll_after_interference','first_world_nll_after_revisit',
          'attempted_updates','replay_steps')
    aggregate={name:{key:_summarize([r['models'][name][key] for r in individual])
                     for key in keys} for name in names}
    result={'experiment':'PhiDevelopmentalIntelligenceMesh','version':'0.2.0',
            'method':'predefined sequential synthetic worlds; isolated database per model and seed',
            'start_seed':start_seed,'runs':runs,'samples_per_phase':samples,'capacity':capacity,
            'aggregate':aggregate,'per_seed':individual,
            'metric_definitions':{
                'forgetting_delta_nll':'first-world NLL after third world MINUS NLL after initial training; lower is better',
                'relearning_delta_nll':'first-world NLL after third world MINUS NLL after first-world revisit; higher is better',
                'new_world_accuracy':'mean accuracy immediately after training each newly introduced world (second and third)',
                'attempted_updates':'training/replay link-update attempts through third phase, including rejected updates',
                'replay_steps':'extra rehearsal attempts (not compute matched)'},
            'limitations':['Synthetic fixed-label six-state worlds, not general learning or human brain development.',
                           'Fixed learner is intentionally stable on old knowledge because it refuses new links when full.',
                           'Rehearsal gets additional update attempts; reported models are not compute-matched.',
                           'Paired seeds are repeatable but do not establish significance or external validity.',
                           'Hyperparameters should be preregistered before selecting a preferred strategy.',
                           'No LLM weight updates, continuous neuroscience model, or consciousness claims.']}
    if output is not None:
        out=Path(output);out.mkdir(parents=True,exist_ok=True)
        (out/'study.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
        (out/'study.html').write_text(render_study(result),encoding='utf-8')
        (out/'review_packet.md').write_text(render_review(result),encoding='utf-8')
    return result


def render_review(result: dict) -> str:
    lines=['# Φ Developmental Mesh: multi-seed study','',
           f"Runs: {result['runs']}; seeds {result['start_seed']}–{result['start_seed']+result['runs']-1}; {result['samples_per_phase']} training samples/phase.",
           '', '| Model | Forgetting ΔNLL (mean ± SD) | New-world accuracy (mean ± SD) | Attempted updates |',
           '| --- | ---: | ---: | ---: |']
    for name,metrics in result['aggregate'].items():
        def pair(metric):
            a=metrics[metric];return f"{a['mean']:.3f} ± {a['sample_std']:.3f}"
        lines.append(f"| {name} | {pair('forgetting_delta_nll')} | {pair('new_world_accuracy')} | {metrics['attempted_updates']['mean']:.0f} |")
    lines.extend(['','## Interpretation safeguards','',*(f'- {x}' for x in result['limitations']),
                  '', '## Human reviewer questions','','- Does the baseline make learning new worlds artificially difficult?',
                  '- Can rehearsal be matched for total update attempts and memory?',
                  '- Do results persist with stochastic transitions and genuinely novel states?',
                  '- Was this study preregistered before any parameter selection?'])
    return '\n'.join(lines)+'\n'


def render_study(data: dict) -> str:
    rows=[]
    for name,stats in data['aggregate'].items():
        f=stats['forgetting_delta_nll'];a=stats['new_world_accuracy'];u=stats['attempted_updates']
        rows.append('<tr><th scope="row">'+html.escape(name)+'</th>'+
                    f'<td>{f["mean"]:.3f} ± {f["sample_std"]:.3f}</td>'+
                    f'<td>{a["mean"]:.3f} ± {a["sample_std"]:.3f}</td>'+
                    f'<td>{u["mean"]:.0f}</td></tr>')
    bars=[]
    for idx,(name,stats) in enumerate(data['aggregate'].items()):
        val=max(0,min(1,stats['new_world_accuracy']['mean']))
        bars.append(f'<div class="barrow"><span>{html.escape(name)}</span><div class="track"><div class="fill" style="width:{100*val:.1f}%"></div></div><b>{val:.2f}</b></div>')
    notes=''.join('<li>'+html.escape(x)+'</li>' for x in data['limitations'])
    return '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Φ Developmental Study</title><style>
    :root{color-scheme:dark;font-family:system-ui, sans-serif;background:#0d1420;color:#eaf1ff}body{max-width:1050px;padding:30px 20px;margin:auto;line-height:1.55}h1{font-size:clamp(2rem,4vw,3.5rem);margin-bottom:0}h2{margin-top:2rem}p,li{color:#bdc9dd}.eyebrow{letter-spacing:.2em;color:#8ad6e3;font-weight:700;font-size:.85rem}table{width:100%%;border-collapse:collapse;margin:2rem 0}td,th{padding:14px;text-align:left;border-bottom:1px solid #2b405b}thead{color:#8ad6e3}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}.card{border:1px solid #314a65;border-radius:14px;padding:20px;background:#152238}.card b{display:block;font-size:1.6rem}.barrow{display:flex;align-items:center;gap:12px;margin:16px 0}.barrow span{min-width:165px;font-size:.82rem}.track{height:13px;border-radius:12px;flex:1;background:#273751;overflow:hidden}.fill{height:100%%;background:linear-gradient(90deg,#5bbcc9,#a5a4ff)}.barrow b{min-width:36px}.note{background:#1d293c;padding:15px;border-left:3px solid #8ad6e3;border-radius:8px}footer{margin:3rem 0 1rem;color:#9ba9be} </style></head><body>
    <div class="eyebrow">PHI369 LABS • REPRODUCIBLE RESEARCH</div><h1>Growing is not the same as remembering.</h1><p>Offline, multi-seed continual-learning study. The goal: measure both adaptation and retention, not manufacture a victory for one learner.</p>
    <section class="cards"><div class="card">Seeds<b>%s</b>Independent repeated synthetic runs</div><div class="card">Training events / phase<b>%s</b>Identical examples within each seed</div><div class="card">Connection budget<b>%s</b>Same maximum links per learner</div></section>
    <h2>Adaptation to new worlds</h2><p>Mean immediate held-out accuracy, averaged across the second and third worlds. Higher is better.</p>%s
    <h2>Memory versus learning</h2><p>Forgetting: first-world held-out NLL increase from initial training to after the third world; lower is better. Mean ± sample standard deviation.</p>
    <table><thead><tr><th>Model</th><th>Forgetting ΔNLL</th><th>New-world accuracy</th><th>Update attempts</th></tr></thead><tbody>%s</tbody></table>
    <p class="note">The fixed model can look exceptionally good at remembering because it rejects new links when full. Replay uses extra update attempts. This is not a compute-matched comparison.</p><h2>Scientific limitations</h2><ul>%s</ul><footer>All data synthetic, all experiments offline. No claim of intelligence equivalent to human cognition.</footer></body></html>'''%(data['runs'],data['samples_per_phase'],data['capacity'],''.join(bars),''.join(rows),notes)
