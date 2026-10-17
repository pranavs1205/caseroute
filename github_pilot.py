"""CLI for the bounded getzep/graphiti pilot; never publishes to GitHub."""
import argparse
import json
import os
from pathlib import Path

from graph import Store
from repo_pilot import RepoPilot


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('command',choices=['sync','status','search','refresh'])
    parser.add_argument('value',nargs='?',default='')
    parser.add_argument('--issues-only',action='store_true')
    parser.add_argument('--live',action='store_true')
    parser.add_argument('--receipt',help='Optional local JSON receipt path')
    args=parser.parse_args()
    pilot=RepoPilot(Store(os.getenv('CASE_GITHUB_GRAPH','caseroute_github')))
    if args.command=='sync':result=pilot.sync(not args.issues_only)
    elif args.command=='status':result=pilot.stats()
    elif args.command=='search':result=pilot.search(args.value,args.live)
    else:result=pilot.refresh(int(args.value))
    if args.receipt:
        path=Path(args.receipt);path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
