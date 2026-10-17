import unittest
from uuid import uuid4

from components import enrich, mentions
from graph import Store
from landscape import Landscape
from llm import investigate
from real_cases import RealCases


class ConnectedLandscape(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.store = Store('caseroute_landscape_test_' + uuid4().hex)
        cls.rows = [dict(id='a', title='Python streaming DataFrame from Kafka', description=''),
                    dict(id='b', title='Python streaming Kafka retry', description='A SQL reader issue'),
                    dict(id='c', title='Kafka broker error', description='')]
        s=cls.store
        s.write("CREATE (:Dataset {id:'test-source', name:'Test source', url:'https://example.com', revision:'fixture', license:'fixture'}), (:Project {id:'test-project', name:'Test project'}), (:Version {id:'test:1',name:'1.0'})")
        for row in cls.rows:
            s.write('''CREATE (i:HistoricalIssue {id:$id, title:$title, description:$description,
                search_text:$search, resolution:'Fixed', priority:'Major', status:'Resolved', url:'https://example.com'})
                WITH i MATCH (v:Version {id:'test:1'}), (d:Dataset {id:'test-source'}), (p:Project {id:'test-project'})
                CREATE (i)-[:AFFECTS]->(v), (i)-[:SOURCED_FROM]->(d), (i)-[:IN_PROJECT]->(p)''',
                    **row, search=row['title'].lower())
        enrich(s, cls.rows)
        cls.real=RealCases(s)
        cls.landscape=Landscape(cls.real)

    @classmethod
    def tearDownClass(cls):
        cls.store.graph.delete()

    def test_mentions_have_exact_source_evidence_and_do_not_match_substrings(self):
        found=mentions(dict(id='x', title='kafkastore parquetish', description='Python and Kafka'))
        self.assertEqual({m['component'] for m in found}, {'pyspark','kafka'})
        self.assertTrue(all(m['matched'] in m['excerpt'] and m['field']=='description' for m in found))

    def test_enrichment_is_idempotent(self):
        before=self.store.read('MATCH ()-[r:MENTIONS]->() RETURN count(r) AS n')[0]['n']
        enrich(self.store,self.rows)
        after=self.store.read('MATCH ()-[r:MENTIONS]->() RETURN count(r) AS n')[0]['n']
        self.assertEqual(before,after)

    def test_component_intersection_and_boundary_decision(self):
        context=self.real.context('a')
        self.assertEqual(len(context['components']),4)
        self.assertEqual([r['id'] for r in context['component_related']],['b'])
        r=investigate(self.real,'Python streaming DataFrame from Kafka',False,'a')
        self.assertEqual(r['decision']['next_step'],'investigate_component_boundary')
        self.assertIn('Kafka',r['decision']['action'])
        self.assertTrue(any(t['tool']=='find_component_intersections' for t in r['trace']))

    def test_full_projection_uses_collection_rows_and_preserves_every_link(self):
        r=self.landscape.projection()
        self.assertEqual(r['issue_count'],3)
        ids={n['id'] for n in r['nodes']}
        self.assertTrue(all(e['source'] in ids and e['target'] in ids for e in r['edges']))
        self.assertEqual(sum(e['kind']=='MENTIONS' for e in r['edges']),9)
        bulk=[t for t in r['trace'] if t['tool']=='load_all_issue_nodes'][0]
        self.assertEqual(bulk['rows'],1)
        self.assertEqual(bulk['records'],3)

    def test_focused_projection_keeps_mention_excerpts(self):
        r=self.landscape.projection('a')
        self.assertTrue(any(e['kind']=='MENTIONS' and e['excerpt'] for e in r['edges']))
        self.assertEqual(r['seed'],'a')
        self.assertGreaterEqual(len(self.landscape.examples()),1)


if __name__=='__main__':
    unittest.main()
