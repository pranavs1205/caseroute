"""Replay the exposed 20 cases for development, never overwrite the baseline.

This is explicitly in-sample: implementation changes were motivated by these
failures. It cannot establish held-out accuracy or independent quality gains.
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

from graph import Store
from investigation_policy import VERSION
from llm import investigate
from real_cases import RealCases


def main():
    root=Path('evaluation/real')
    immutable=['plan.json','labels.csv','labels.lock.json','graph_predictions.json','post_review_graph.csv','summary.json']
    hashes={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in immutable}
    plan=json.loads((root/'plan.json').read_text(encoding='utf-8'))
    labels={r['case_id']:r for r in json.loads((root/'labels.lock.json').read_text(encoding='utf-8'))['labels']}
    out=Path('evaluation/development')/(VERSION+'.json')
    if out.exists():
        raise SystemExit('Development receipt already exists. Preserve it; use a new policy version for later experiments.')
    real=RealCases(Store())
    rows=[]
    for case in plan['cases']:
        started=perf_counter()
        result=investigate(real,case['report'],False,case['issue_id'])
        decision=result['decision']
        rows.append(dict(case_id=case['case_id'],issue_id=case['issue_id'],action=decision['next_step'],
                         reasons=decision['guidance']['reasons'],
                         primary_components=[c['name'] for c in decision['guidance']['primary_components']],
                         action_enum_agreement=decision['next_step'] in labels[case['case_id']]['acceptable_steps'].split(';'),
                         must_abstain=labels[case['case_id']]['must_abstain']=='yes',
                         ranked_evidence=result['context'].get('ranked_evidence',[])[:5],
                         run_id=result['id'],latency_ms=round((perf_counter()-started)*1000,2)))
    assert hashes=={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in immutable}
    summary=dict(policy=VERSION,created=datetime.now(timezone.utc).isoformat(),condition='graph-only in-sample development replay',
                 caveat='Not held-out, independent or LLM quality evaluation. Original 20-case artifacts remain unchanged.',
                 baseline_hashes=hashes,completed=len(rows),action_enum_agreement=sum(r['action_enum_agreement'] for r in rows),
                 required_abstentions=sum(r['must_abstain'] for r in rows),
                 requested_required_abstentions=sum(r['must_abstain'] and r['action']=='request_details' for r in rows),results=rows)
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k!='results'},indent=2))


if __name__=='__main__':
    main()
