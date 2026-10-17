"""Live FalkorDB gates. Isolated disposable graph; never touches the demo graph."""
import unittest
from uuid import uuid4
from graph import Store
from seed import seed


class GraphFlows(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.store = Store('caseroute_test_' + uuid4().hex)
        seed(cls.store)

    @classmethod
    def tearDownClass(cls):
        cls.store.graph.delete()

    def test_evidence_memory_and_owner_mutation(self):
        s = self.store
        cid = s.create_case('discounts', 'Checkout fails with discount')
        result = s.investigate(cid)
        self.assertEqual(result['status'], 'ready')
        self.assertEqual(result['action']['id'], 'pricing-cache')
        self.assertEqual(result['action']['source'], 'RUN-101')
        self.assertTrue(result['action']['past_cases'])
        s.attempt(cid, 'pricing-cache', 'failed', 'Versions match')
        reopened = Store(s.graph.name).investigate(cid)
        self.assertEqual(reopened['action']['id'], 'pricing-rule')
        self.assertEqual(len(reopened['history']), 1)
        s.change_owner('pricing', 'platform')
        self.assertIn('Platform Reliability', s.investigate(cid)['draft'])
        s.change_owner('pricing', 'commerce')

    def test_ambiguity_and_invalid_service(self):
        cid = self.store.create_case('campaign', 'Campaign checkout fails')
        self.assertEqual(self.store.investigate(cid)['status'], 'needs_service')
        self.assertIsNone(self.store.investigate(cid)['action'])
        resolved = self.store.investigate(cid, 'campaigns')
        self.assertEqual(resolved['action']['id'], 'campaign-window')
        with self.assertRaises(ValueError):
            self.store.investigate(cid, 'pricing')

    def test_impact_is_read_only_and_multi_hop(self):
        before = self.store.read('MATCH (n) RETURN count(n) AS n')[0]['n']
        result = self.store.impact('pricing')
        after = self.store.read('MATCH (n) RETURN count(n) AS n')[0]['n']
        self.assertEqual(before, after)
        self.assertTrue(any(p['services'] == ['Campaigns', 'Checkout', 'Pricing API'] for p in result['paths']))
        self.assertTrue(any(p['services'] == ['Pricing API'] for p in result['paths']))

    def test_seed_does_not_reset_memory_or_owner(self):
        cid = self.store.create_case('discounts', 'Discount fails again')
        self.store.attempt(cid, 'pricing-cache', 'inconclusive', 'No trace available')
        self.store.change_owner('pricing', 'platform')
        seed(self.store)
        result = self.store.investigate(cid)
        self.assertEqual(len(result['history']), 1)
        self.assertIn('Platform Reliability', result['draft'])
        self.store.change_owner('pricing', 'commerce')

    def test_conflicting_owners_hold_handoff_and_can_be_repaired(self):
        s = self.store
        s.write("MATCH (s:Service {id:'pricing'}), (t:Team {id:'growth'}) CREATE (s)-[:OWNED_BY {source:'CONFLICT-FIXTURE', updated:'2026-10-15'}]->(t)")
        cid = s.create_case('discounts', 'Discount fails with conflicting ownership')
        self.assertEqual(s.investigate(cid)['status'], 'ownership_conflict')
        self.assertIsNone(s.investigate(cid)['draft'])
        s.change_owner('pricing', 'commerce')
        repaired = s.investigate(cid)
        self.assertEqual(len(repaired['owners']), 1)
        self.assertEqual(repaired['status'], 'ready')

    def test_source_freshness_is_flagged(self):
        s = self.store
        s.write("MATCH (:Service {id:'pricing'})-[r:OWNED_BY]->() SET r.updated='2020-01-01'")
        cid = s.create_case('discounts', 'Discount fails with old owner record')
        self.assertTrue(s.investigate(cid)['warnings'])
        s.change_owner('pricing', 'commerce')

    def test_exhausted_actions_and_missing_owner_do_not_invent_handoff(self):
        s = self.store
        cid = s.create_case('discounts', 'Every check has failed')
        for aid in ['pricing-cache', 'pricing-rule']:
            s.attempt(cid, aid, 'failed', 'Still broken')
        self.assertEqual(s.investigate(cid)['status'], 'exhausted')
        self.assertIsNone(s.investigate(cid)['draft'])
        s.write("MATCH (:Service {id:'pricing'})-[r:OWNED_BY]->() DELETE r")
        self.assertEqual(s.investigate(cid)['status'], 'missing_owner')
        s.change_owner('pricing', 'commerce')


if __name__ == '__main__':
    unittest.main()
