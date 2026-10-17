"""Live real-data schema and policy checks on an isolated, tiny graph fixture."""
import unittest
from unittest.mock import patch
from uuid import uuid4

from graph import Store
from llm import Decision, LLMUnavailable, SearchPlan, investigate
from real_cases import RealCases


class RealEvidenceFlows(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.store = Store('caseroute_real_test_' + uuid4().hex)
        cls.store.write('''CREATE (d:Dataset {id:'fixture', url:'https://example.com/data.csv', revision:'test', license:'fixture'})
            CREATE (p:Project {id:'test', name:'Fixture project'})
            CREATE (v:Version {id:'test:3.4.0', name:'3.4.0'})-[:VERSION_OF]->(p)
            CREATE (i:HistoricalIssue {id:'test-1', title:'PySpark Python compatibility', description:'Fixture description',
                search_text:'pyspark python compatibility fixture description', status:'Resolved', resolution:'Fixed',
                priority:'Major', created:'24/Feb/23 03:04', resolved:'24/Feb/23 05:15', record:2, url:'https://example.com/1'})
            CREATE (other:HistoricalIssue {id:'test-2', title:'Unrelated symptom on same version', resolution:'Duplicate', url:'https://example.com/2'})
            CREATE (i)-[:AFFECTS]->(v), (other)-[:AFFECTS]->(v), (i)-[:IN_PROJECT]->(p), (i)-[:SOURCED_FROM]->(d)''')
        cls.real = RealCases(cls.store)

    @classmethod
    def tearDownClass(cls):
        cls.store.graph.delete()

    def test_version_path_adds_evidence_not_in_text_search(self):
        matches = self.real.search('pyspark', '3.4.0')
        self.assertEqual([r['id'] for r in matches], ['test-1'])
        trace = []
        context = self.real.context('test-1', trace)
        self.assertEqual(context['related'][0]['id'], 'test-2')
        self.assertEqual(context['related'][0]['shared_versions'], ['3.4.0'])
        self.assertEqual(len(trace), 6)
        self.assertTrue(all(s['cypher'] and s['duration_ms'] >= 0 for s in trace))
        self.assertEqual(context['issue']['resolution'], 'Fixed')
        self.assertNotIn('owner', context['issue'])

    def test_human_review_changes_next_action_and_run_survives_new_client(self):
        self.real.review('test-1', 'not_applicable', 'Different environment; do not repeat this lead')
        r = investigate(self.real, 'pyspark failure', False, 'test-1')
        self.assertEqual(r['decision']['next_step'], 'request_details')
        self.assertTrue(any(s['tool'] == 'apply_review_memory' for s in r['trace']))
        loaded = RealCases(Store(self.store.graph.name)).run(r['id'])
        self.assertEqual(loaded['decision'], r['decision'])
        self.assertEqual(loaded['trace'], r['trace'])
        self.assertEqual(loaded['context'], r['context'])
        self.assertEqual(loaded['matches'], r['matches'])
        self.assertFalse(any(s['kind'] == 'llm' for s in loaded['trace']))

    def test_no_match_requests_details(self):
        r = investigate(self.real, 'unfindablezzztoken', False)
        self.assertIsNone(r['context'])
        self.assertEqual(r['decision']['next_step'], 'request_details')
        self.assertEqual(r['decision']['evidence_ids'], [])

    def test_llm_cannot_cite_unknown_issue(self):
        outputs = [SearchPlan(terms=['pyspark'], version=None), Decision(next_step='check_environment', evidence_ids=['invented'])]
        with patch('llm.generate', side_effect=outputs), self.assertRaises(LLMUnavailable):
            investigate(self.real, 'pyspark failure', True, 'test-1')

    def test_llm_cannot_invent_affected_version(self):
        with patch('llm.generate', return_value=SearchPlan(terms=['pyspark'], version='99.9.9')), self.assertRaises(LLMUnavailable):
            investigate(self.real, 'pyspark failure', True)

    def test_llm_cannot_add_factual_diagnosis_to_output(self):
        with self.assertRaises(ValueError):
            Decision.model_validate(dict(next_step='check_environment', evidence_ids=['test-1'], summary='Invented root cause'))


if __name__ == '__main__':
    unittest.main()
