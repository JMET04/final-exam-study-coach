"""Verify that administrative events cannot advance a student's learning."""
from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'skills/final-exam-study-coach/scripts/update_study_state.py'

class Progress(unittest.TestCase):
    def update(self,result,kind):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'state.json'
            before={'status':'can_explain','next_review':'2030-01-01','last_practiced':'2026-01-01','evidence':['previous independent response']}
            p.write_text(json.dumps({'course':'test','topics':{'neutral-axis':before.copy()},'sessions':[]}),encoding='utf-8')
            subprocess.run([sys.executable,str(SCRIPT),str(p),'--topic','neutral-axis','--result',result,'--confidence','5','--evidence-kind',kind],check=True,capture_output=True)
            return before,json.loads(p.read_text(encoding='utf-8'))
    def test_display_feedback_and_migration_preserve_learning(self):
        for kind in ['self_report','teaching_output','teacher_feedback','preparation','migration']:
            before,after=self.update('correct',kind)
            self.assertEqual(before,after['topics']['neutral-axis'])
            self.assertFalse(after['sessions'][-1]['mastery_updated'])
    def test_missed_task_does_not_restart_review_clock(self):
        before,after=self.update('missed','independent_response')
        for key in ['status','next_review','last_practiced','evidence']:
            self.assertEqual(before[key],after['topics']['neutral-axis'][key])
        self.assertEqual(after['topics']['neutral-axis']['missed_count'],1)
    def test_new_independent_response_can_update(self):
        before,after=self.update('correct','independent_response')
        self.assertNotEqual(before['status'],after['topics']['neutral-axis']['status'])
        self.assertTrue(after['sessions'][-1]['mastery_updated'])

if __name__=='__main__': unittest.main()
