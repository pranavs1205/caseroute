import unittest
from unittest.mock import patch,MagicMock
from uuid import uuid4

from github_client import GitHubClient,REPOSITORY
from graph import Store
from repo_pilot import RepoPilot,parse_symbols,choose_files


def issue(number,title,body):
    return dict(number=number,title=title,body=body,state='open',html_url=f'https://github.com/{REPOSITORY}/issues/{number}',updated_at='2026-10-18T00:00:00Z')


class GitHubScope(unittest.TestCase):
    def test_search_cannot_inject_repository_or_pull_request_scope(self):
        client=GitHubClient(credential='')
        with patch.object(client,'get',return_value=dict(items=[],incomplete_results=False)) as get:
            client.search('repo:other/private OR is:pr add_episode')
        path=get.call_args.args[0]
        from urllib.parse import parse_qs,urlsplit
        query=parse_qs(urlsplit(path).query)['q'][0]
        self.assertIn('repo:'+REPOSITORY,query)
        self.assertIn('is:issue',query)
        self.assertNotIn('repo:other',query)
        self.assertNotIn(' OR ',query)

    def test_paths_outside_repository_are_rejected_before_network(self):
        with self.assertRaises(ValueError):GitHubClient(credential='').get('/repos/other/private/issues')

    def test_static_parse_does_not_execute_top_level_code(self):
        result=parse_symbols('example.py','raise RuntimeError("must never run")\nclass Widget:\n def add_episode(self):\n  return load_record()\n')
        method=next(s for s in result if s['name']=='add_episode')
        self.assertEqual(method['qualified'],'Widget.add_episode')
        self.assertIn('load_record',method['calls'])

    def test_bounded_selection_keeps_entrypoint_search_and_tests(self):
        paths=[dict(path='graphiti_core/graphiti.py'),dict(path='graphiti_core/search/search.py'),
               *[dict(path=f'graphiti_core/driver/falkordb/operations/op_{n}.py') for n in range(30)],
               dict(path='tests/test_search.py')]
        chosen=choose_files(paths)
        self.assertLessEqual(len(chosen),16)
        for path in ['graphiti_core/graphiti.py','graphiti_core/search/search.py','tests/test_search.py']:
            self.assertIn(path,[x['path'] for x in chosen])


class RepositoryGraph(unittest.TestCase):
    def setUp(self):
        self.store=Store('caseroute_repo_test_'+uuid4().hex)
        self.pilot=RepoPilot(self.store);self.pilot.index()
        self.store.write('MERGE (r:PilotRepository {id:$repo}) SET r.commit=$sha',repo=REPOSITORY,sha='fixture-commit')
        self.pilot.upsert_issue(issue(1,'Graphiti.add_episode fails with CustomDriverError','The driver operation fails during an explicit reproduction. Capture the installed package version and compare the graph configuration.'))
        self.pilot.upsert_issue(issue(2,'Other CustomDriverError in add_episode','A separate report using add_episode has similar symptoms but does not establish the same cause.'))
        self.pilot.store_file('graphiti_core/example.py','class Graphiti:\n def add_episode(self):\n  return driver_read()\ndef caller():\n return add_episode()\n','fixture-commit')
        self.pilot.degrees()

    def tearDown(self):self.store.graph.delete()

    def test_new_report_uses_graph_issue_and_code_paths_and_survives_reload(self):
        result=self.pilot.create('Graphiti.add_episode fails with CustomDriverError','I can reproduce this while adding an episode with the driver configured. Expected persistence does not happen; the operation raises CustomDriverError.','0.x')
        self.assertTrue(result['run']['issues'])
        self.assertTrue(any(x['symbol']=='Graphiti.add_episode' for x in result['run']['code']))
        self.assertTrue(result['run']['possible_callers'])
        self.assertEqual(result['run']['github_calls'],0)
        self.assertEqual(RepoPilot(Store(self.store.graph.name)).case(result['intake']['id'])['run'],result['run'])

    def test_known_issue_is_excluded_and_observation_changes_action(self):
        result=self.pilot.create('Graphiti.add_episode fails with CustomDriverError','The operation fails in a reproducible example with the configured driver. Compare expected persistence and actual failure before making a change.',source_number=1)
        self.assertNotIn(f'{REPOSITORY}#1',[x['id'] for x in result['run']['issues']])
        self.assertEqual(result['run']['decision']['next_step'],'review_recorded_resolution')
        changed=self.pilot.observe(result['intake']['id'],'not_applicable','Version differs; do not reuse this lead.',0)
        self.assertEqual(changed['run']['decision']['next_step'],'request_details')
        with self.assertRaises(ValueError):self.pilot.observe(result['intake']['id'],'useful_lead','Stale write must fail.',0)

    def test_sparse_report_skips_llm_and_does_not_become_searchable_source(self):
        with patch('repo_pilot.generate') as model:
            result=self.pilot.create('A completely new failure','')
            result=self.pilot.investigate(result['intake']['id'],True)
        model.assert_not_called()
        self.assertEqual(result['run']['decision']['next_step'],'request_details')
        self.assertEqual(len(self.pilot.search('completely new failure')['results']),0)

    def test_code_snapshot_is_idempotent_and_old_commits_are_not_returned(self):
        self.pilot.store_file('graphiti_core/example.py','def add_episode():\n return 1\n','older-commit')
        result=self.pilot.create('add_episode fails in driver','The operation produces an exception instead of writing the record. The same reproduction succeeds with an earlier configuration; compare package and driver versions.')
        self.assertTrue(result['run']['code'])
        self.assertTrue(all('fixture-commit' in x['url'] for x in result['run']['code']))

    def test_live_search_is_cached_and_foreign_issue_cannot_be_imported(self):
        mock=type('FakeClient',(),{'receipts':[{}],'search':lambda self,k,l:dict(query='fixture query',items=[issue(3,'New add_episode lead','Public test source')],incomplete=False)})()
        self.pilot.client_factory=lambda:mock
        self.assertEqual(self.pilot.search('add_episode',True)['github_calls'],1)
        self.assertEqual(self.pilot.search('add_episode',True)['github_calls'],0)
        wrong=issue(4,'Foreign','');wrong['html_url']='https://github.com/other/repo/issues/4'
        with self.assertRaises(ValueError):self.pilot.upsert_issue(wrong)

    def test_direct_lookup_and_reference_refresh(self):
        self.assertEqual(self.pilot.search('#1')['results'][0]['number'],1)
        self.pilot.upsert_issue(issue(1,'Source add_episode','See #2 for another reported failure.'))
        self.pilot.degrees()
        self.assertEqual(self.store.read('MATCH ()-[r:REFERENCES]->() RETURN count(r) AS n')[0]['n'],1)
        self.pilot.upsert_issue(issue(1,'Source add_episode','Reference removed in the updated source.'))
        self.assertEqual(self.store.read('MATCH ()-[r:REFERENCES]->() RETURN count(r) AS n')[0]['n'],0)

    def test_issues_only_sync_preserves_existing_code_snapshot(self):
        self.store.write('MATCH (r:PilotRepository) SET r.coverage=$coverage',coverage='{"indexed_files":1}')
        client=MagicMock();client.get.return_value=dict(private=False,description='fixture',license={})
        client.search.return_value=dict(items=[],incomplete=False);client.receipts=[]
        self.pilot.client_factory=lambda:client
        result=self.pilot.sync(False)
        self.assertEqual(result['snapshot']['commit'],'fixture-commit')
        self.assertEqual(result['snapshot']['coverage'],'{"indexed_files":1}')


if __name__=='__main__':unittest.main()
