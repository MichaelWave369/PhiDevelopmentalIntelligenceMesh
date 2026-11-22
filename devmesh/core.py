"""SQLite-backed, bounded associative learner. Not a neural or biological brain."""
from __future__ import annotations

import math
import random
import sqlite3
from pathlib import Path

SCHEMA = '''
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS links (
  world TEXT NOT NULL, source TEXT NOT NULL, dest TEXT NOT NULL,
  strength REAL NOT NULL CHECK(strength > 0), touched INTEGER NOT NULL,
  protected INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY(world,source,dest)
);
CREATE TABLE IF NOT EXISTS experiences (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  world TEXT NOT NULL, source TEXT NOT NULL, dest TEXT NOT NULL,
  approved INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS experiences_world_idx ON experiences(world);
CREATE TABLE IF NOT EXISTS counters (name TEXT PRIMARY KEY, value INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS audit (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  kind TEXT NOT NULL, detail TEXT NOT NULL
);
'''


class DevelopmentalLearner:
    """Structural adaptation with a strict link budget and optional rehearsal.

    A 'link' is a frequency estimate, not a synapse. No model weights are updated.
    """

    def __init__(self, db: str | Path, *, capacity: int = 12, pruning: bool = True,
                 replay: int = 0, seed: int = 369, memory_limit: int = 512):
        if capacity < 1 or replay < 0 or memory_limit < 1:
            raise ValueError('capacity and memory_limit must be positive; replay nonnegative')
        self.path = str(db)
        self.capacity = capacity
        self.pruning = pruning
        self.replay = replay
        self.memory_limit = memory_limit
        self.rng = random.Random(seed)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.conn.execute('INSERT OR IGNORE INTO counters VALUES (?,?)', ('step',0))
        self.conn.execute('INSERT OR IGNORE INTO counters VALUES (?,?)', ('grown',0))
        self.conn.execute('INSERT OR IGNORE INTO counters VALUES (?,?)', ('pruned',0))
        self.conn.execute('INSERT OR IGNORE INTO counters VALUES (?,?)', ('rejected',0))
        self.conn.execute('INSERT OR IGNORE INTO counters VALUES (?,?)', ('replayed',0))
        self.conn.commit()

    def close(self):
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def _increment(self, label: str, count: int = 1) -> None:
        self.conn.execute('UPDATE counters SET value=value+? WHERE name=?',(count,label))

    def _step(self):
        self._increment('step')
        return int(self.conn.execute("SELECT value FROM counters WHERE name='step'").fetchone()[0])

    def _insert_link(self, world, source, dest, approved=False):
        tick = self._step()
        existing = self.conn.execute('SELECT strength,protected FROM links WHERE world=? AND source=? AND dest=?',
                                     (world,source,dest)).fetchone()
        if existing:
            self.conn.execute('UPDATE links SET strength=strength+1,touched=?,protected=? WHERE world=? AND source=? AND dest=?',
                              (tick, int(approved or bool(existing['protected'])),world,source,dest))
            return
        size = self.conn.execute('SELECT COUNT(*) FROM links').fetchone()[0]
        if size >= self.capacity:
            if not self.pruning:
                self._increment('rejected')
                return
            # Never evict teacher-protected links. Deterministic tie-breaking.
            candidate = self.conn.execute('''SELECT world,source,dest FROM links WHERE protected=0
                ORDER BY strength/((1.0+(?-touched)/3.0)*(1.0+(?-touched)/3.0)), touched,world,source,dest LIMIT 1''',(tick,tick)).fetchone()
            if candidate is None:
                self._increment('rejected')
                return
            self.conn.execute('DELETE FROM links WHERE world=? AND source=? AND dest=?', tuple(candidate))
            self._increment('pruned')
        self.conn.execute('INSERT INTO links VALUES (?,?,?,?,?,?)',
                          (world,source,dest,1.0,tick,int(approved)))
        self._increment('grown')

    def observe(self, world: str, source: str, destination: str, *, teacher_approved: bool=False) -> None:
        """Store *training* observations only. Held-out evaluation must call predict()."""
        if not all(isinstance(x,str) and 0 < len(x) <= 120 for x in (world,source,destination)):
            raise ValueError('labels must be nonempty strings of at most 120 characters')
        with self.conn:
            self._insert_link(world,source,destination,teacher_approved)
            self.conn.execute('INSERT INTO experiences(world,source,dest,approved) VALUES (?,?,?,?)',
                              (world,source,destination,int(teacher_approved)))
            # Bound durable episodic memory, retain approved examples first.
            excess = self.conn.execute('SELECT MAX(COUNT(*)-?,0) FROM experiences',(self.memory_limit,)).fetchone()[0]
            if excess:
                self.conn.execute('''DELETE FROM experiences WHERE id IN (
                    SELECT id FROM experiences WHERE approved=0 ORDER BY id LIMIT ?)''',(excess,))
                remaining_excess = self.conn.execute('SELECT MAX(COUNT(*)-?,0) FROM experiences', (self.memory_limit,)).fetchone()[0]
                if remaining_excess:
                    self.conn.execute('''DELETE FROM experiences WHERE id IN (
                        SELECT id FROM experiences ORDER BY id LIMIT ?)''',(remaining_excess,))
            if self.replay:
                # Stable pseudo-random selection from prior observations only, across all worlds.
                records = self.conn.execute('SELECT world,source,dest FROM experiences ORDER BY id').fetchall()
                for _ in range(self.replay):
                    item = records[self.rng.randrange(len(records))]
                    self._insert_link(item['world'],item['source'],item['dest'])
                    self._increment('replayed')

    def probabilities(self, world: str, source: str, states: tuple[str,...]) -> dict[str,float]:
        if not states or len(set(states))!=len(states):
            raise ValueError('states must be nonempty and unique')
        rows = self.conn.execute('SELECT dest,strength FROM links WHERE world=? AND source=?',
                                (world,source)).fetchall()
        counts = {r['dest']:r['strength'] for r in rows}
        alpha = 0.2
        total = alpha * len(states) + sum(counts.get(x,0) for x in states)
        return {x:(alpha+counts.get(x,0))/total for x in states}

    def predict(self, world: str, source: str, states: tuple[str,...]) -> str:
        probs = self.probabilities(world,source,states)
        return max(states, key=lambda item: probs[item])

    def score(self, world: str, events: list[tuple[str,str]], states: tuple[str,...]) -> dict:
        if not events:
            raise ValueError('no evaluation events')
        loss = 0.0; correct = 0
        for source,dest in events:
            probs = self.probabilities(world,source,states)
            if dest not in probs:
                raise ValueError('unknown destination')
            loss -= math.log(probs[dest])
            correct += self.predict(world,source,states) == dest
        return {'nll':round(loss/len(events),5),'accuracy':round(correct/len(events),5)}

    def metrics(self) -> dict:
        counters = {r['name']:r['value'] for r in self.conn.execute('SELECT * FROM counters')}
        count = self.conn.execute('SELECT COUNT(*) FROM links').fetchone()[0]
        protected = self.conn.execute('SELECT COUNT(*) FROM links WHERE protected=1').fetchone()[0]
        experiences = self.conn.execute('SELECT COUNT(*) FROM experiences').fetchone()[0]
        return {**counters,'links':count,'protected':protected,'experiences':experiences,'capacity':self.capacity}

    def audit(self, action: str, detail: str):
        with self.conn:
            self.conn.execute('INSERT INTO audit(kind,detail) VALUES (?,?)',(action,detail[:1000]))
