"""Reproducible continual-learning benchmark; all scores are held-out."""
import hashlib
import json
import random
import tempfile
from pathlib import Path
from .core import DevelopmentalLearner

STATES = tuple('ABCDEF')
RULES = {
    'first_world':dict(zip(STATES,'BCDEFA')),
    'second_world':dict(zip(STATES,'FEDCBA')),
    'third_world':dict(zip(STATES,'CDEFAB')),
}
PHASES = ('first_world','second_world','third_world','first_world')


def _rng(seed,scope):
    digest = hashlib.sha256(f'{seed}:{scope}'.encode()).digest()
    return random.Random(int.from_bytes(digest[:8],'big'))


def cases(world,count,seed,scope):
    rng = _rng(seed,f'{world}:{scope}')
    mapping = RULES[world]
    return [(s,mapping[s]) for s in rng.choices(STATES,k=count)]


def run_benchmark(*, seed=369, output=None, samples=180, capacity=9):
    """Equal-capacity fixed/plastic/rehearsal models. Extra replay steps disclosed."""
    if samples < 10 or capacity < 1:
        raise ValueError('samples >= 10 and capacity >= 1 required')
    validation = {name:cases(name,360,seed,'HOLDOUT-NEVER-TRAIN') for name in RULES}
    result = {'experiment':'PhiDevelopmentalIntelligenceMesh','version':'0.1.0',
              'seed':seed,'samples_per_phase':samples,'capacity':capacity,
              'models':['fixed','grow_prune','grow_prune_replay'], 'phases':[],
              'limitations':['Synthetic six-state deterministic mappings, not general intelligence.',
                  'State/label alphabets fixed; no novel ontology, neurons, or weights.',
                  'Replay model uses additional learning updates (not compute-matched).',
                  'No human learning, brain development, sentience, or biological evidence.']}
    with tempfile.TemporaryDirectory() as tmp:
        configs=[('fixed',False,0),('grow_prune',True,0),('grow_prune_replay',True,2)]
        models={name:DevelopmentalLearner(Path(tmp)/f'{name}.sqlite',capacity=capacity,
                    pruning=prune,replay=replay,seed=seed) for name,prune,replay in configs}
        try:
            for index,world in enumerate(PHASES):
                for src,dst in cases(world,samples,seed,f'train-{index}'):
                    for model in models.values():
                        model.observe(world,src,dst)
                # Explicit persistence check: restart between phases.
                for name,model in list(models.items()):
                    model.close()
                    prune,replay = next((p,r) for n,p,r in configs if n==name)
                    models[name]=DevelopmentalLearner(Path(tmp)/f'{name}.sqlite',capacity=capacity,
                                pruning=prune,replay=replay,seed=seed+index+1)
                result['phases'].append({'stage':index+1,'trained_world':world,
                    'models':{name:{'scores':{w:model.score(w,validation[w],STATES) for w in RULES},
                                    'metrics':model.metrics()} for name,model in models.items()}})
        finally:
            for model in models.values():model.close()
    if output:
        dest=Path(output);dest.mkdir(parents=True,exist_ok=True)
        (dest/'results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
        (dest/'review_packet.md').write_text(review_packet(result),encoding='utf-8')
        (dest/'report.html').write_text(render_html(result),encoding='utf-8')
    return result


def review_packet(data):
    last=data['phases'][-1]
    rows=['# Developmental Mesh evidence review','','Human review requested; no autonomous actions or model training occurred.','',
          f"Seed: {data['seed']}; last phase: {last['trained_world']}",'',
          '| configuration | links | first-world held-out NLL | first-world accuracy |',
          '| --- | ---: | ---: | ---: |']
    for n,r in last['models'].items():
        s=r['scores']['first_world'];m=r['metrics']
        rows.append(f"| {n} | {m['links']} | {s['nll']:.5f} | {s['accuracy']:.5f} |")
    rows.extend(['','Critique experimental leakage, capacity fairness, replay compute, hyperparameters, and alternative explanations.',
                 'Suggest falsifiable follow-up experiments. Do not infer consciousness or human-like development.'])
    return '\n'.join(rows)+'\n'


def render_html(data):
    import html
    rows=[]
    for p in data['phases']:
        for name,r in p['models'].items():
            s=r['scores']['first_world'];m=r['metrics']
            rows.append('<tr>' + ''.join(f'<td>{html.escape(str(x))}</td>' for x in
                         (p['stage'],p['trained_world'],name,m['links'],m['grown'],m['pruned'],m['replayed'],s['nll'],s['accuracy'])) + '</tr>')
    return '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Φ Developmental Mesh Report</title><style>body{background:#10151f;color:#eef3fa;font:16px system-ui;margin:4rem auto;max-width:1060px;padding:0 1rem}table{width:100%%;border-collapse:collapse}td,th{border-bottom:1px solid #334255;padding:12px;text-align:left}th{color:#b9c9e1}h1{color:#d5dcff}.sub{color:#aebaca}a{color:#c5d2ff}</style><h1>Φ Developmental Intelligence Mesh</h1><p class="sub">Seed %s · capacity %s · fixed synthetic rules · lower NLL is better</p><table><thead><tr><th>Phase</th><th>World</th><th>Learner</th><th>Links</th><th>Grown</th><th>Pruned</th><th>Replay</th><th>First-world NLL</th><th>Accuracy</th></tr></thead><tbody>%s</tbody></table><p class="sub">This experiment does not demonstrate neural or biological development, agency, or consciousness.</p></html>'''%(data['seed'],data['capacity'],''.join(rows))
