import unittest
from unittest.mock import patch, MagicMock
from uuid import uuid4

from evidence_graph import enrich, identifiers, ranked_neighbors
from graph import Store
from investigation_policy import guidance
from real_cases import RealCases
from llm import investigate, SearchPlan, Decision, LLMUnavailable


def context(title, description, components=None):
    return dict(issue=dict(title=title, description=description), components=components or [], memory=[])


class EvidenceGates(unittest.TestCase):
    def test_sparse_and_title_only_sources_require_details(self):
        for description in ('', 'Rename TinyObject to BetterObject'):
            result=guidance(context('Rename TinyObject to BetterObject', description))
            self.assertEqual(result['allowed_steps'], ['request_details'])

    def test_maintenance_is_not_treated_as_incident(self):
        result=guidance(context('Migrate widget command to new framework',
            'Introduce a logical command, replace the old statement parser and remove obsolete checks from the analyzer while preserving the existing public behavior.'))
        self.assertEqual(result['recommended'], 'review_recorded_resolution')

    def test_stack_noise_cannot_enable_component_boundary(self):
        components=[dict(name='Scheduler',field='description',excerpt='at org.apache.spark.scheduler.DAGScheduler (DAGScheduler.scala:200)'),
                    dict(name='Shuffle',field='description',excerpt='org.apache.spark.shuffle.Writer.write(Writer.java:12)'),
                    dict(name='Python',field='title',excerpt='Python integration fails')]
        result=guidance(context('Python integration fails',
            'A user sees different column names after converting the input dataset. Reproduce the transformation and compare expected output labels against the observed result.',components))
        self.assertNotIn('investigate_component_boundary',result['allowed_steps'])

    def test_identifier_extraction_preserves_source_and_skips_stack_frames(self):
        row=dict(id='sample',title='TinyReaderSuite fails',description='Missing CustomCryptoProvider\n at org.example.NoisySuite.run(NoisySuite.java:7)\n22949 [info] at java.base/java.lang.ClassLoader.loadClass(ClassLoader.java:525)')
        signals=identifiers(row)
        self.assertTrue(any(s['value']=='CustomCryptoProvider' for s in signals))
        self.assertTrue(all(s['matched'] in s['excerpt'] for s in signals))
        self.assertFalse(any('NoisySuite' in s['value'] for s in signals))
        self.assertFalse(any('ClassLoader' in s['value'] for s in signals))

    def test_missing_dependency_outweighs_component_count(self):
        components=[dict(name=n,field='title',excerpt=n) for n in ['Hive','ORC','SQL']]
        result=guidance(context('Hive ORC SQL test fails',
            'Writing the example dataset terminates with NoClassDefFoundError for CustomCryptoProvider. Inspect the runtime dependency configuration and reproduce with the required library present.',components))
        self.assertEqual(result['recommended'],'check_environment')
        self.assertNotIn('investigate_component_boundary',result['allowed_steps'])

    def test_sparse_gate_skips_decision_model_call(self):
        real=MagicMock()
        c=context('Small test fails','')
        c['issue'].update(id='fixture')
        real.context.return_value=c
        real.search.return_value=[]
        real.save_run.return_value='fixture-run'
        with patch('llm.generate',return_value=SearchPlan(terms=['Small'],version=None)) as model:
            result=investigate(real,'Small test fails',True,'fixture')
        self.assertEqual(model.call_count,1)  # Planning only; no decision call.
        self.assertEqual(result['decision']['next_step'],'request_details')
        self.assertFalse(result['decision']['llm_selected_step'])

    def test_long_source_line_keeps_match_inside_excerpt(self):
        signals=identifiers(dict(id='long',title='Report',description='plain '*300+'CustomCryptoProvider'))
        self.assertTrue(signals)
        self.assertTrue(all(s['matched'] in s['excerpt'] for s in signals))

    def test_model_receives_ranked_paths_and_cannot_bypass_boundary_gate(self):
        real=MagicMock()
        c=context('Read operation fails','A read operation fails when converting an input record to the output representation. Compare the exact error, runtime release, expected schema and reproduction before proposing any remediation.')
        c.update(versions=[],related=[],component_related=[],ranked_evidence=[dict(id='ranked',paths=[dict(signal='TinyReaderSuite',degree=2)])])
        c['issue'].update(id='source',resolution='Fixed')
        real.context.return_value=c;real.search.return_value=[]
        outputs=[SearchPlan(terms=['read'],version=None),Decision(next_step='investigate_component_boundary',evidence_ids=['ranked'])]
        with patch('llm.generate',side_effect=outputs) as model, self.assertRaises(LLMUnavailable):
            investigate(real,'Read operation fails',True,'source')
        self.assertEqual(model.call_args.args[2]['ranked_evidence'][0]['id'],'ranked')
        self.assertIn('ranked',model.call_args.kwargs['allowed_ids'])
        self.assertNotIn('investigate_component_boundary',model.call_args.kwargs['allowed_steps'])


class GraphRanking(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.store=Store('caseroute_ranking_test_'+uuid4().hex)
        cls.rows=[dict(id='source',title='RareReaderSuite and BroadTaskSuite',description=''),
                  dict(id='specific',title='RareReaderSuite',description=''),
                  *[dict(id=f'hub-{n}',title='BroadTaskSuite',description='') for n in range(20)]]
        for row in cls.rows:
            cls.store.write('CREATE (:HistoricalIssue {id:$id,title:$title,description:$description})',**row)
        enrich(cls.store,cls.rows)

    @classmethod
    def tearDownClass(cls):
        cls.store.graph.delete()

    def test_rare_path_beats_popular_hub_and_source_is_excluded(self):
        trace=[]
        rows=ranked_neighbors(RealCases(self.store),'source',trace)
        self.assertEqual(rows[0]['id'],'specific')
        self.assertNotIn('source',[r['id'] for r in rows])
        self.assertEqual(rows[0]['paths'][0]['degree'],2)
        self.assertIn('HAS_SIGNAL',trace[0]['cypher'])

    def test_reenrichment_does_not_change_degrees_or_duplicate_edges(self):
        before=self.store.read('MATCH ()-[e:HAS_SIGNAL]->() RETURN count(e) AS n')
        enrich(self.store,self.rows)
        self.assertEqual(before,self.store.read('MATCH ()-[e:HAS_SIGNAL]->() RETURN count(e) AS n'))
        self.assertEqual(ranked_neighbors(RealCases(self.store),'source')[0]['paths'][0]['degree'],2)


if __name__=='__main__':
    unittest.main()
