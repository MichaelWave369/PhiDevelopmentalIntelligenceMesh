"""Read-only, explicit integrations to existing local tools; no hidden data movement."""
from __future__ import annotations
import csv
import json
import math
import sqlite3
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import build_opener, ProxyHandler, Request


def mesh_status(url: str = 'http://127.0.0.1:4765') -> dict:
    """GET public /status from local Mesh. No messages or user data are read."""
    parts=urlparse(url)
    if parts.scheme != 'http' or parts.hostname not in ('127.0.0.1','localhost') or parts.username or parts.password or parts.query or parts.fragment or parts.path not in ('','/'):
        raise ValueError('Only local Mesh HTTP origins are accepted')
    opener=build_opener(ProxyHandler({}))
    with opener.open(Request(url.rstrip('/')+'/api/v1/status',method='GET'),timeout=3) as response:
        return json.loads(response.read(65536))


def buddy_counts(path: str|Path) -> dict:
    """Read only table counts, no conversation text, no database mutation."""
    path=Path(path).resolve()
    if not path.is_file():raise FileNotFoundError(path)
    uri=path.as_uri().replace('file:///','file:///')+'?mode=ro'
    with sqlite3.connect(uri,uri=True) as db:
        tables={row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        return {k:db.execute(f'SELECT COUNT(*) FROM {k}').fetchone()[0]
                for k in ('sessions','messages','deliberation_events') if k in tables}


def emergence_worlds(folder: str|Path) -> dict:
    """Validate official PhiEmergence v1.0 exports; don't overwrite source kernels."""
    folder=Path(folder)
    atlas={}
    with (folder/'complete_stationary_atlas_v1.0.csv').open(newline='',encoding='utf-8') as f:
        for r in csv.DictReader(f):
            k=(r['model'],r['law'])
            atlas.setdefault(k,[]).append((r['key'],float(r['pi'])))
    flows={}
    with (folder/'complete_probability_flows_v1.0.csv').open(newline='',encoding='utf-8') as f:
        for r in csv.DictReader(f):
            k=(r['model'],r['law'])
            rate=float(r['rate'])
            if not math.isfinite(rate) or rate<=0:raise ValueError('invalid positive rate')
            flows.setdefault(k,{}).setdefault(r['source'],[]).append((r['destination'],rate))
    if len(atlas)!=4 or set(atlas)!=set(flows):raise ValueError('expected 4 PhiEmergence worlds')
    result={}
    for key,states in atlas.items():
        names={x for x,_ in states}
        if abs(sum(y for _,y in states)-1)>1e-7: raise ValueError('unnormalized stationary weights')
        if names != set(flows[key]):raise ValueError('incomplete source states')
        if any(dst not in names for group in flows[key].values() for dst,_ in group):raise ValueError('invalid destination')
        result['/'.join(key)]={'states':len(states),'transitions':sum(len(g) for g in flows[key].values())}
    return result


def coherence_summary(csv_path: str|Path) -> dict:
    """Independent read-only inspection, not a developmental mechanism."""
    path=Path(csv_path)
    with path.open(newline='',encoding='utf-8') as f:
        reader=csv.DictReader(f)
        rows=list(reader)
    return {'rows':len(rows),'columns':reader.fieldnames,'source':path.name,
            'note':'Independent transport data; no evidence for brain quantum effects.'}
