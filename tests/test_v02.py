import json
import tempfile
import unittest
from pathlib import Path
from devmesh.core import DevelopmentalLearner
from devmesh.tutor import SpacedTutor
from devmesh.study import run_study,render_study


class TutorTests(unittest.TestCase):
    def test_enroll_and_due_hide_answer(self):
        with DevelopmentalLearner(':memory:') as learner:
            tutor=SpacedTutor(learner)
            card=tutor.enroll('shapes','triangle','3-sides',provenance='teacher-approved')
            questions=tutor.due()
            self.assertEqual(len(questions),1)
            self.assertEqual(questions[0]['id'],card)
            self.assertNotIn('expected',questions[0])
            self.assertNotIn('provenance',questions[0])
            self.assertEqual(learner.predict('shapes','triangle',('3-sides','4-sides')),'3-sides')
            self.assertEqual(learner.metrics()['protected'],1)

    def test_incorrect_answer_reinforces_approved_only(self):
        with DevelopmentalLearner(':memory:') as learner:
            tutor=SpacedTutor(learner)
            card=tutor.enroll('shapes','triangle','3-sides',provenance='manual')
            outcome=tutor.answer(card,'4-sides')
            self.assertFalse(outcome['correct'])
            self.assertEqual(outcome['expected'],'3-sides')
            self.assertEqual(outcome['next_due_tick'],2)
            self.assertEqual(tutor.summary()['attempts'],1)
            self.assertEqual(tutor.summary()['successes'],0)
            self.assertEqual(learner.conn.execute("SELECT COUNT(*) FROM links WHERE dest='4-sides'").fetchone()[0],0)
            self.assertEqual(tutor.due(),[])
            tutor.advance()
            self.assertEqual(len(tutor.due()),1)
            success=tutor.answer(card,'3-sides')
            self.assertTrue(success['correct'])
            self.assertEqual(success['next_due_tick'],5)
            self.assertEqual(tutor.summary()['successes'],1)
            with self.assertRaises(ValueError):tutor.answer(card,'3-sides')

    def test_protected_budget_exhaustion_rejected(self):
        with DevelopmentalLearner(':memory:',capacity=1) as learner:
            tutor=SpacedTutor(learner)
            tutor.enroll('w','one','A',provenance='manual')
            with self.assertRaisesRegex(ValueError,'link budget full'):
                tutor.enroll('w','two','B',provenance='manual')
            self.assertEqual(tutor.summary()['total'],1)

    def test_restart_persists_clock_and_card(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'learner.sqlite'
            with DevelopmentalLearner(path) as learner:
                t=SpacedTutor(learner)
                c=t.enroll('words','hello','greeting',provenance='manual book')
                t.answer(c,'greeting')
            with DevelopmentalLearner(path) as learner:
                t=SpacedTutor(learner)
                self.assertEqual(t.tick,1)
                self.assertEqual(t.summary()['total'],1)
                self.assertEqual(t.due(),[])
                t.advance(2)
                self.assertEqual(t.due()[0]['id'],c)

    def test_conflicts_are_rejected_and_duplicates_idempotent(self):
        with DevelopmentalLearner(':memory:') as learner:
            t=SpacedTutor(learner)
            card=t.enroll('w','s','a',provenance='teacher 1')
            self.assertEqual(card,t.enroll('w','s','a',provenance='teacher 2'))
            self.assertEqual(t.summary()['total'],1)
            with self.assertRaisesRegex(ValueError,'conflicting lesson'):
                t.enroll('w','s','b',provenance='teacher 3')
            with self.assertRaises(ValueError):t.enroll('w','s','a',provenance='')
            with self.assertRaises(ValueError):t.advance(0)


class StudyTests(unittest.TestCase):
    def test_study_repeatable_and_shows_tradeoffs(self):
        a=run_study(start_seed=369,runs=2,samples=10,capacity=9)
        b=run_study(start_seed=369,runs=2,samples=10,capacity=9)
        self.assertEqual(a,b)
        self.assertEqual(len(a['per_seed']),2)
        self.assertGreater(a['aggregate']['grow_prune_replay']['replay_steps']['mean'],0)
        self.assertGreater(a['aggregate']['fixed']['first_world_nll_after_revisit']['mean'],0)
        self.assertIn('not compute-matched',render_study(a))

    def test_study_outputs(self):
        with tempfile.TemporaryDirectory() as d:
            run_study(start_seed=23,runs=2,samples=10,output=d)
            for artifact in ('study.html','study.json','review_packet.md'):
                self.assertTrue((Path(d)/artifact).is_file())
            data=json.loads((Path(d)/'study.json').read_text())
            self.assertEqual(data['runs'],2)

    def test_invalid_args(self):
        with self.assertRaises(ValueError):run_study(runs=1)
        with self.assertRaises(ValueError):run_study(samples=1,runs=2)


if __name__=='__main__':unittest.main()
