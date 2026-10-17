"""CLI for the bounded getzep/graphiti pilot; never publishes to GitHub."""
import argparse
import json
import os
from pathlib import Path

from graph import Store
from repositories import RepositoryRegistry
from github_client import REPOSITORY


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('command',choices=['add','list','sync','status','search','refresh'])
    parser.add_argument('value',nargs='?',default='')
    parser.add_argument('--repo',default=REPOSITORY)
    parser.add_argument('--all',action='store_true',help='Continue issue batches until pagination is exhausted')
    parser.add_argument('--restart',action='store_true',help='Restart issue pagination from page one')
    parser.add_argument('--issues-only',action='store_true')
    parser.add_argument('--live',action='store_true')
    parser.add_argument('--receipt',help='Optional local JSON receipt path')
    args=parser.parse_args()
    registry=RepositoryRegistry()
    pilot=registry.pilot(args.repo) if args.command not in ('add','list') else None
    if args.command=='add':result=registry.add(args.value or args.repo)
    elif args.command=='list':result=registry.list()
    elif args.command=='sync':
        result=pilot.sync(not args.issues_only,restart=args.restart)
        receipts=list(result['receipts']);pages=result['pages_imported']
        while args.all and not result['issues_complete']:
            print('Issue backfill progress:',result['snapshot'].get('issue_pages',0),'pages',flush=True)
            result=pilot.sync(False)
            receipts.extend(result['receipts']);pages+=result['pages_imported']
        result.update(receipts=receipts,github_calls=len(receipts),pages_imported=pages)
    elif args.command=='status':result=pilot.stats()
    elif args.command=='search':result=pilot.search(args.value,args.live)
    else:result=pilot.refresh(int(args.value))
    if args.receipt:
        path=Path(args.receipt);path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
