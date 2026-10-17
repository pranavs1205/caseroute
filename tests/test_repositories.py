import unittest
from unittest.mock import patch
from uuid import uuid4

from graph import Store
from github_client import GitHubClient,GitHubUnavailable,normalize_repository
from repositories import RepositoryRegistry
from repo_pilot import RepoPilot


def item(repo,number,title='SharedReader fails'):
    return dict(number=number,title=title,body='A reproducible failure occurs while reading the input record. Compare the actual runtime and expected behavior before treating another report as a diagnosis.',
                state='open',html_url=f'https://github.com/{repo}/issues/{number}',updated_at='2026-10-18T00:00:00Z')


class Normalization(unittest.TestCase):
    def test_urls_and_case_are_normalized(self):
        self.assertEqual(normalize_repository('https://github.com/Owner/Project.git/'),'owner/project')

    def test_non_github_hosts_and_path_traversal_are_rejected(self):
        for value in ['https://evil.example/a/b','a/../b','a/.','https://github.com/a/b?token=x','a/b/issues/1']:
            with self.subTest(value=value),self.assertRaises(ValueError):normalize_repository(value)

    def test_repository_list_pagination_filters_prs(self):
        c=GitHubClient(credential='',repository='example/repo');c.has_next=True
        with patch.object(c,'get',return_value=[item('example/repo',1),{**item('example/repo',2),'pull_request':{}}]) as get:
            result=c.issue_page(4)
        self.assertEqual([i['number'] for i in result['items']],[1])
        self.assertTrue(result['has_next'])
        self.assertIn('state=all',get.call_args.args[0]);self.assertIn('page=4',get.call_args.args[0])


class RepositoryIsolation(unittest.TestCase):
    def setUp(self):
        self.graphs=[];self.mapping={}
        self.catalog=Store('caseroute_catalog_test_'+uuid4().hex);self.graphs.append(self.catalog)
        def store(repo):
            if repo not in self.mapping:
                self.mapping[repo]=Store('caseroute_multi_test_'+uuid4().hex);self.graphs.append(self.mapping[repo])
            return self.mapping[repo]
        class Client:
            receipts=[]
            def __init__(self,repo):self.repo=repo
            def get(self,path):return dict(full_name=self.repo,private=False,language='Python',description='fixture')
        self.registry=RepositoryRegistry(self.catalog,store,lambda repo:Client(repo))
        self.registry.initialize()

    def tearDown(self):
        for store in self.graphs:store.graph.delete()

    def test_add_is_idempotent_and_repo_case_memory_is_isolated(self):
        self.registry.add('example/first');self.registry.add('https://github.com/example/first')
        self.registry.add('example/second')
        a=self.registry.pilot('example/first');b=self.registry.pilot('example/second')
        a.upsert_issue(item('example/first',1));a.degrees()
        b.upsert_issue(item('example/second',1));b.degrees()
        ca=a.create('SharedReader fails on my input','The input read operation fails during reproduction. Expected data is present, but loading stops with an exception. Compare versions and exact source behavior.')
        self.assertTrue(all(x['id'].startswith('example/first#') for x in ca['run']['issues']))
        self.assertEqual(b.cases(),[])
        with self.assertRaises(KeyError):b.case(ca['intake']['id'])
        hits=self.registry.search_all('SharedReader')['results']
        self.assertEqual({h['repository'] for h in hits},{'example/first','example/second'})
        self.assertEqual(len([r for r in self.registry.list() if r['repository']['id']=='example/first']),1)

    def test_private_repo_is_not_registered(self):
        class Client:
            def get(self,path):return dict(full_name='example/private',private=True)
        self.registry.client_factory=lambda repo:Client()
        with self.assertRaises(ValueError):self.registry.add('example/private')
        self.assertFalse(any(r['repository']['id']=='example/private' for r in self.registry.list()))

    def test_cursor_resumes_after_failure_and_completion_is_explicit(self):
        repo='example/pages';store=Store('caseroute_pages_test_'+uuid4().hex);self.graphs.append(store)
        class Client:
            def __init__(self):self.receipts=[];self.fail=False;self.pages=[]
            def get(self,path):return dict(private=False,license={},description='fixture')
            def issue_page(self,page):
                self.pages.append(page)
                if self.fail:raise GitHubUnavailable('Fixture rate limit')
                return dict(items=[item(repo,page)],has_next=page<3,records=1)
        client=Client();p=RepoPilot(store,lambda:client,repository=repo)
        first=p.sync(False,max_pages=1)
        self.assertFalse(first['issues_complete']);self.assertEqual(first['snapshot']['next_issue_page'],2)
        client.fail=True
        with self.assertRaises(GitHubUnavailable):p.sync(False,max_pages=1)
        self.assertEqual(p.stats()['snapshot']['next_issue_page'],2)
        client.fail=False
        second=RepoPilot(Store(store.graph.name),lambda:client,repository=repo).sync(False,max_pages=2)
        self.assertTrue(second['issues_complete']);self.assertEqual(second['counts']['RepoIssue'],3)
        self.assertEqual(client.pages,[1,2,2,3])
        p.sync(False,max_pages=2)
        self.assertEqual(client.pages,[1,2,2,3])
        p.sync(False,max_pages=1,restart=True)
        self.assertEqual(p.stats()['snapshot']['next_issue_page'],2)

    def test_cached_results_can_be_paginated_past_thirty(self):
        self.registry.add('example/many');p=self.registry.pilot('example/many')
        # Minimal fixture fields exercise the search paging independently of extraction.
        rows=[dict(id=f'example/many#{n}',number=n) for n in range(35)]
        p.store.write("UNWIND $rows AS row CREATE (:RepoIssue {id:row.id,number:row.number,title:'SharedReader',body:'fixture',updated:'2026'})",rows=rows)
        first=p.search('SharedReader');second=p.search('SharedReader',offset=first['next_offset'])
        self.assertEqual(len(first['results']),30);self.assertTrue(first['has_more'])
        self.assertEqual(len(second['results']),5);self.assertFalse(second['has_more'])
        self.assertFalse({i['id'] for i in first['results']}&{i['id'] for i in second['results']})


if __name__=='__main__':unittest.main()
