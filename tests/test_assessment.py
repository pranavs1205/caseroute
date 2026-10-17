"""Assessment gates, without generating predictions or touching real labels."""
import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import real_evaluation as assessment


class AssessmentIntegrity(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.patch=patch.object(assessment,'ROOT',self.root);self.patch.start()
        self.plan={'protocol':'known_history_investigation_v1','cases':[{'case_id':f'R{i:02}'} for i in range(1,21)]}
        self.plan['sha256']=assessment.digest(self.plan)
        assessment.write_json(self.root/'plan.json',self.plan)
        self.labels=[dict(case_id=f'R{i:02}',reviewer='Human fixture',reviewer_kind='human',acceptable_steps='request_details',must_abstain='yes',relevant_issue_ids='',missing_information='version',rationale='Fixture only') for i in range(1,21)]

    def tearDown(self):
        self.patch.stop();self.tmp.cleanup()

    def save_labels(self):
        with (self.root/'labels.csv').open('w',newline='',encoding='utf-8') as file:
            writer=csv.DictWriter(file,fieldnames=list(self.labels[0]));writer.writeheader();writer.writerows(self.labels)

    def test_runner_refuses_missing_prelabels_before_calling_agent(self):
        with patch.object(assessment,'investigate') as agent,self.assertRaises(SystemExit):assessment.run_assessment(False)
        agent.assert_not_called()

    def test_blank_human_labels_are_not_accepted(self):
        self.labels[0]['reviewer']='';self.save_labels()
        with self.assertRaises(SystemExit):assessment.lock()
        self.assertFalse((self.root/'labels.lock.json').exists())

    def test_label_changes_after_lock_are_rejected(self):
        self.save_labels();assessment.lock();self.labels[0]['acceptable_steps']='check_environment';self.save_labels()
        with patch.object(assessment,'investigate') as agent,self.assertRaises(SystemExit):assessment.run_assessment(False)
        agent.assert_not_called()

    def test_summary_does_not_invent_scores_for_unjudged_cases(self):
        self.save_labels();assessment.lock()
        assessment.write_json(self.root/'graph_predictions.json',dict(results=[{'case_id':'R01','result':None,'error':'Provider failed'}]))
        assessment.summarize()
        summary=json.loads((self.root/'summary.json').read_text())['summaries'][0]
        self.assertEqual(summary['completed'],0)
        self.assertEqual(summary['postrun_judged'],0)
        self.assertEqual(len(summary['failures']),1)


if __name__=='__main__':unittest.main()
