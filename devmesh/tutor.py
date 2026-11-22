"""Explicit teacher-approved, local spaced-practice curriculum.

This is a deterministic exercise scheduler, not a model that matures biologically.
No personal data, chat transcript, or external content is auto-imported.
"""
from __future__ import annotations

from .core import DevelopmentalLearner

TUTOR_SCHEMA = '''
CREATE TABLE IF NOT EXISTS practice_clock (
    id INTEGER PRIMARY KEY CHECK (id = 1), tick INTEGER NOT NULL CHECK(tick >= 0)
);
INSERT OR IGNORE INTO practice_clock VALUES (1, 0);
CREATE TABLE IF NOT EXISTS practice_cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    world TEXT NOT NULL, source TEXT NOT NULL, expected TEXT NOT NULL,
    provenance TEXT NOT NULL, due_tick INTEGER NOT NULL DEFAULT 0,
    streak INTEGER NOT NULL DEFAULT 0, attempts INTEGER NOT NULL DEFAULT 0,
    successes INTEGER NOT NULL DEFAULT 0,
    UNIQUE(world,source,expected)
);
CREATE INDEX IF NOT EXISTS practice_due_idx ON practice_cards(due_tick,id);
CREATE TABLE IF NOT EXISTS practice_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    card_id INTEGER NOT NULL REFERENCES practice_cards(id),
    tick INTEGER NOT NULL,
    correct INTEGER NOT NULL CHECK(correct IN (0,1))
);
'''


def _label(value: str, name: str, limit: int = 120) -> str:
    if not isinstance(value, str) or not (0 < len(value.strip()) <= limit):
        raise ValueError(f'{name} must be a nonempty string of at most {limit} characters')
    return value.strip()


class SpacedTutor:
    """Uses the learner's same SQLite database. Clock ticks are exercise steps, not days."""

    def __init__(self, learner: DevelopmentalLearner):
        self.learner = learner
        self.conn = learner.conn
        self.conn.executescript(TUTOR_SCHEMA)

    @property
    def tick(self) -> int:
        return int(self.conn.execute('SELECT tick FROM practice_clock WHERE id=1').fetchone()[0])

    def enroll(self, world: str, source: str, expected: str, *, provenance: str) -> int:
        """A human explicitly approves a lesson and its source; no silent ingestion."""
        world = _label(world, 'world')
        source = _label(source, 'source')
        expected = _label(expected, 'expected')
        provenance = _label(provenance, 'provenance', 250)
        # Prevent giving two incompatible expected labels to one prompt.
        conflict = self.conn.execute('SELECT id,expected FROM practice_cards WHERE world=? AND source=?',
                                     (world,source)).fetchone()
        if conflict and conflict['expected'] != expected:
            raise ValueError('conflicting lesson: this source already has a different expected answer')
        if conflict is None:
            # Approved associations are protected; report budget exhaustion instead
            # of quietly scheduling a card the learner cannot ever encode.
            link = self.conn.execute('''SELECT 1 FROM links WHERE world=? AND source=? AND dest=?''',
                                     (world,source,expected)).fetchone()
            occupied = self.conn.execute('SELECT COUNT(*) FROM links').fetchone()[0]
            can_evict = self.conn.execute('SELECT COUNT(*) FROM links WHERE protected=0').fetchone()[0]
            if not link and occupied >= self.learner.capacity and (not self.learner.pruning or not can_evict):
                raise ValueError('link budget full of protected links; cannot enroll new lesson')
        with self.conn:
            self.conn.execute('''INSERT OR IGNORE INTO practice_cards
                (world,source,expected,provenance,due_tick) VALUES (?,?,?,?,?)''',
                (world,source,expected,provenance,self.tick))
            row = self.conn.execute('SELECT id FROM practice_cards WHERE world=? AND source=? AND expected=?',
                                    (world,source,expected)).fetchone()
        if not conflict:
            self.learner.observe(world,source,expected,teacher_approved=True)
            self.learner.audit('lesson-enrolled',f'card={row[0]}; provenance={provenance}')
        return int(row[0])

    def due(self, *, limit: int=10) -> list[dict]:
        """Return prompts without answer keys or provenance; avoids accidental answer leakage."""
        if not (1 <= limit <= 100):
            raise ValueError('limit must be between 1 and 100')
        return [dict(row) for row in self.conn.execute('''
            SELECT id,world,source,due_tick,streak FROM practice_cards
            WHERE due_tick<=? ORDER BY due_tick,id LIMIT ?''', (self.tick,limit))]

    def advance(self, steps: int=1) -> int:
        """Advance *simulated* practice time, not wall-clock time."""
        if not isinstance(steps,int) or not (1 <= steps <= 100000):
            raise ValueError('steps must be between 1 and 100000')
        with self.conn:
            self.conn.execute('UPDATE practice_clock SET tick=tick+? WHERE id=1',(steps,))
        return self.tick

    def answer(self, card_id: int, response: str) -> dict:
        response = _label(response,'response')
        card = self.conn.execute('SELECT * FROM practice_cards WHERE id=?',(card_id,)).fetchone()
        if card is None:
            raise ValueError('unknown lesson card')
        if card['due_tick'] > self.tick:
            raise ValueError(f'lesson not due until simulated step {card["due_tick"]}')
        correct = response == card['expected']
        next_streak = card['streak']+1 if correct else 0
        # A review at step T costs one scheduler tick. Good answers double the interval.
        new_tick = self.tick + 1
        interval = min(64,2**next_streak) if correct else 1
        with self.conn:
            self.conn.execute('UPDATE practice_clock SET tick=? WHERE id=1',(new_tick,))
            self.conn.execute('''UPDATE practice_cards SET due_tick=?,streak=?,attempts=attempts+1,
                successes=successes+? WHERE id=?''',
                (new_tick+interval,next_streak,int(correct),card_id))
            self.conn.execute('INSERT INTO practice_attempts(card_id,tick,correct) VALUES (?,?,?)',
                              (card_id,new_tick,int(correct)))
        # Constructive correction is given only for a teacher-approved card.
        # Rehearsal strengthens the approved association even on a wrong answer.
        self.learner.observe(card['world'],card['source'],card['expected'],teacher_approved=True)
        return {'id':card_id,'correct':correct,'expected':card['expected'],
                'next_due_tick':new_tick+interval,'streak':next_streak,'clock':new_tick,
                'feedback':'Correct. Nice work.' if correct else 'Not yet. Review the approved answer and try again.'}

    def summary(self) -> dict:
        cards = self.conn.execute('''SELECT COUNT(*) AS total,COALESCE(SUM(attempts),0) AS attempts,
            COALESCE(SUM(successes),0) AS successes,
            COALESCE(SUM(CASE WHEN due_tick<=? THEN 1 ELSE 0 END),0) AS due
            FROM practice_cards''',(self.tick,)).fetchone()
        return {'tick':self.tick,**dict(cards)}
