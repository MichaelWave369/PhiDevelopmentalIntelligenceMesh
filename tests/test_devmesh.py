import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from devmesh.core import DevelopmentalLearner
from devmesh.benchmark import run_benchmark
from devmesh.bridges import mesh_status,buddy_counts,emergence_worlds,coherence_summary

class CoreTests(unittest.TestCase):
    def test_growth_budget_pruning_and_protection(self):
        with tempfile.TemporaryDirectory() as d:
            with DevelopmentalLearner(Path(d)/'a.db',capacity=2) as m:
                m.observe('a','x','A',teacher_approved=True)
                m.observe('a','y','B')
                m.observe('a','z','C')
                self.assertEqual(m.metrics()['links'],2)
                self.assertEqual(m.metrics()['pruned'],1)
                self.assertEqual(m.metrics()['protected'],1)
                self.assertEqual(m.predict('a','x',('A','B','C')),'A')
    def test_fixed_rejects_when_full(self):
        with DevelopmentalLearner(':memory:',capacity=1,pruning=False) as m:
            m.observe('a','a','a');m.observe('b','b','b')
            self.assertEqual(m.metrics()['rejected'],1)
    def test_restart_persists(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'a.sqlite'
            with DevelopmentalLearner(path) as m:m.observe('world','source','dest')
            with DevelopmentalLearner(path) as m:
                self.assertEqual(m.predict('world','source',('dest','other')),'dest')
                self.assertEqual(m.metrics()['links'],1)
    def test_probability_normalized_and_no_scoring_mutation(self):
        with DevelopmentalLearner(':memory:') as m:
            m.observe('w','x','y')
            before=m.metrics().copy()
            self.assertAlmostEqual(sum(m.probabilities('w','x',('y','z')).values()),1)
            self.assertLess(m.score('w',[('x','y')],('y','z'))['nll'],0.3)
            self.assertEqual(m.metrics(),before)
    def test_replay_counter_and_memory_bound(self):
        with DevelopmentalLearner(':memory:',replay=2,memory_limit=3) as m:
            for i in range(6): m.observe('w',str(i),'a')
            self.assertEqual(m.metrics()['experiences'],3)
            self.assertEqual(m.metrics()['replayed'],12)
    def test_teacher_protected_not_evicted(self):
        with DevelopmentalLearner(':memory:',capacity=1) as m:
            m.observe('a','x','A',teacher_approved=True)
            m.observe('b','y','B')
            self.assertEqual(m.metrics()['rejected'],1)
            self.assertEqual(m.metrics()['protected'],1)
    def test_invalid_label(self):
        with DevelopmentalLearner(':memory:') as m:
            with self.assertRaises(ValueError):m.observe('','x','a')

class BenchmarkTests(unittest.TestCase):
    def test_benchmark_deterministic_and_bounded(self):
        a=run_benchmark(samples=20,seed=369,capacity=9)
        b=run_benchmark(samples=20,seed=369,capacity=9)
        self.assertEqual(a,b)
        self.assertEqual(len(a['phases']),4)
        for phase in a['phases']:
            for stats in phase['models'].values():self.assertLessEqual(stats['metrics']['links'],9)
    def test_artifacts(self):
        with tempfile.TemporaryDirectory() as d:
            run_benchmark(samples=20,output=d)
            for name in ('report.html','results.json','review_packet.md'):
                self.assertTrue((Path(d)/name).is_file())
            self.assertEqual(json.loads((Path(d)/'results.json').read_text())['seed'],369)

class BridgesTests(unittest.TestCase):
    def test_mesh_must_be_loopback(self):
        for url in ('https://example.com','http://8.8.8.8:4765','http://localhost:4765/hack','http://evil@localhost:4765'):
            with self.assertRaises(ValueError):mesh_status(url)
    def test_buddy_read_only(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'b.db'
            with sqlite3.connect(path) as db:db.execute('CREATE TABLE messages(id INTEGER)')
            self.assertEqual(buddy_counts(path),{'messages':0})

if __name__=='__main__':unittest.main()
