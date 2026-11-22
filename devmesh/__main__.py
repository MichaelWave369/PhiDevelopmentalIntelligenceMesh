"""Offline CLI. Does not run or modify an LLM unless a human does so separately."""
import argparse
import json
from pathlib import Path
from .benchmark import run_benchmark
from .bridges import buddy_counts, coherence_summary, emergence_worlds, mesh_status
from .core import DevelopmentalLearner


def main():
    p=argparse.ArgumentParser(prog='python -m devmesh',description='Φ Developmental Intelligence Mesh')
    sub=p.add_subparsers(dest='cmd',required=True)
    b=sub.add_parser('benchmark',help='held-out continual-learning comparison')
    b.add_argument('--seed',type=int,default=369)
    b.add_argument('--capacity',type=int,default=9)
    b.add_argument('--samples',type=int,default=180)
    b.add_argument('--output',type=Path,default=Path('outputs/seed-369'))
    t=sub.add_parser('teach',help='approve one training example; creates persistent local database')
    t.add_argument('--db',type=Path,required=True)
    t.add_argument('--world',required=True)
    t.add_argument('--source',required=True)
    t.add_argument('--dest',required=True)
    t.add_argument('--capacity',type=int,default=100)
    s=sub.add_parser('inspect',help='inspect metrics of a local learning database')
    s.add_argument('--db',type=Path,required=True)
    s.add_argument('--capacity',type=int,default=100)
    m=sub.add_parser('mesh-status',help='read local Sovereign Mesh status only')
    m.add_argument('--url',default='http://127.0.0.1:4765')
    e=sub.add_parser('validate-emergence',help='validate original PhiEmergence exports')
    e.add_argument('--folder',type=Path,required=True)
    c=sub.add_parser('inspect-coherence',help='inspect original Coherence Lab CSV')
    c.add_argument('--csv',type=Path,required=True)
    x=sub.add_parser('inspect-buddy',help='read only PhiBuddy table counts')
    x.add_argument('--db',type=Path,required=True)
    a=p.parse_args()
    if a.cmd=='benchmark':
        r=run_benchmark(seed=a.seed,output=a.output,samples=a.samples,capacity=a.capacity)
        print('Wrote',a.output/'report.html')
        print(json.dumps(r['phases'][-1],indent=2))
    elif a.cmd in ('teach','inspect'):
        a.db.parent.mkdir(parents=True,exist_ok=True) if a.cmd=='teach' else None
        if a.cmd=='inspect' and not a.db.is_file():p.error('database does not exist')
        with DevelopmentalLearner(a.db,capacity=a.capacity) as model:
            if a.cmd=='teach':
                model.observe(a.world,a.source,a.dest,teacher_approved=True)
                model.audit('teacher-approved',f'{a.world}/{a.source}/{a.dest}')
            print(json.dumps(model.metrics(),indent=2))
    elif a.cmd=='mesh-status': print(json.dumps(mesh_status(a.url),indent=2))
    elif a.cmd=='validate-emergence': print(json.dumps(emergence_worlds(a.folder),indent=2))
    elif a.cmd=='inspect-coherence': print(json.dumps(coherence_summary(a.csv),indent=2))
    elif a.cmd=='inspect-buddy':print(json.dumps(buddy_counts(a.db),indent=2))

if __name__=='__main__':main()
