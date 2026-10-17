"""Pre-registered, reviewer-labeled known-history assessment. No invented human scores."""
import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

from components import mentions
from graph import Store
from import_real_data import EXPECTED_SHA256, RAW, REVISION, download, records
from llm import LLMUnavailable, investigate
from real_cases import RealCases
from investigation_policy import VERSION

ROOT=Path(__file__).parent/'evaluation'/'real'
STEPS={'check_environment','review_recorded_resolution','request_details','investigate_component_boundary'}
DEMO_IDS={'spark-13289604','spark-13525982','spark-13596756','spark-13596784','spark-13522896'}


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def write_json(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2),encoding='utf-8')


def prepare():
    plan_path=ROOT/'plan.json'
    if plan_path.exists():
        raise SystemExit('Selection already frozen. Existing assessment was left unchanged.')
    store=Store()
    used={r['id'] for r in store.read('MATCH (:InvestigationRun)-[:EXAMINED]->(i:HistoricalIssue) RETURN DISTINCT i.id AS id')}
    excluded=used|DEMO_IDS
    source=list(records(download()))
    candidates=[r for r in source if r['id'] not in excluded]
    seed='caseroute-known-history-2026-10-17-v1'
    ranked=sorted(candidates,key=lambda r:hashlib.sha256((seed+r['id']).encode()).hexdigest())
    selected=[]
    categories=[('multi_component',lambda r:len(mentions(r))>=3 and len(r['description'])>=100,5),
                ('sparse_description',lambda r:len(r['description'])<40,5),
                ('single_component',lambda r:len(mentions(r))==1 and len(r['description'])>=100,5),
                ('other_context',lambda r:True,5)]
    picked=set()
    for category,condition,count in categories:
        matches=[r for r in ranked if r['id'] not in picked and condition(r)][:count]
        if len(matches)!=count:
            raise ValueError('Insufficient source rows for category '+category)
        for row in matches:
            picked.add(row['id'])
            selected.append(dict(case_id=f'R{len(selected)+1:02}',category=category,issue_id=row['id'],
                                 report=row['title'],source_title=row['title'],description=row['description'],
                                 source_url=row['url'],source_record=row['record'],source_status=row['status'],
                                 source_resolution=row['resolution'],versions=row['versions']))
    plan=dict(protocol='known_history_investigation_v1',created=datetime.now(timezone.utc).isoformat(),
              selection_seed=seed,dataset_revision=REVISION,dataset_sha256=EXPECTED_SHA256,
              excluded_ids=sorted(excluded),case_count=20,
              limitations=['Issues remain in the graph and their IDs are supplied. This is not new-issue retrieval.',
                           'Selection is deterministic and stratified, not a representative random sample.',
                           'Model/policy outputs must not be generated until pre-run labels have been locked.',
                           'Source resolution labels do not establish root cause or a correct fix.'],cases=selected)
    plan['sha256']=digest(plan)
    write_json(plan_path,plan)
    with (ROOT/'labels.csv').open('w',encoding='utf-8',newline='') as output:
        fields=['case_id','reviewer','reviewer_kind','acceptable_steps','must_abstain','relevant_issue_ids','missing_information','rationale']
        writer=csv.DictWriter(output,fieldnames=fields);writer.writeheader()
        for row in selected:writer.writerow({'case_id':row['case_id']})
    lines=['# Blinded source packet','',f"Protocol: known historical issue investigation. Frozen plan: `{plan['sha256']}`.",
           '', 'No CaseRoute answers are included. Fill labels.csv before locking labels. Separate acceptable steps with semicolons.',
           '', 'Allowed steps: '+', '.join(sorted(STEPS))+'.',
           '', 'reviewer_kind: human or ai_assisted. must_abstain: yes/no. relevant_issue_ids may be blank if unknown; this is not a negative relevance judgment.',
           '', 'For every case, record missing information and a rationale. Do not infer a fix from Fixed/Invalid/Duplicate labels.']
    for row in selected:
        lines.extend(['',f"## {row['case_id']} — {row['category']}",'',f"**{row['issue_id']}**: {row['source_title']}",
                      '',f"Source: {row['source_url']}",f"Versions: {', '.join(row['versions']) or 'not recorded'}; status: {row['source_status']}; recorded outcome: {row['source_resolution'] or 'unrecorded'}.",
                      '', 'Source description (quoted; missing text remains missing):','', '```text',row['description'] or '[No description in source]','```'])
    (ROOT/'review_packet.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('Prepared 20 sources with no predictions. Plan hash:',plan['sha256'])


def read_labels(plan):
    with (ROOT/'labels.csv').open(encoding='utf-8-sig',newline='') as source:
        labels=list(csv.DictReader(source))
    if {r['case_id'] for r in labels}!={r['case_id'] for r in plan['cases']} or len(labels)!=20:
        raise SystemExit('Labels must contain exactly the 20 frozen case IDs, once each.')
    for row in labels:
        steps=set(filter(None,(s.strip() for s in row['acceptable_steps'].split(';'))))
        if not row['reviewer'].strip() or row['reviewer_kind'] not in ('human','ai_assisted') or not steps or not steps<=STEPS or row['must_abstain'] not in ('yes','no') or not row['rationale'].strip():
            raise SystemExit('Incomplete or invalid pre-run label for '+row['case_id'])
    return labels


def lock():
    plan=json.loads((ROOT/'plan.json').read_text(encoding='utf-8'))
    if (ROOT/'labels.lock.json').exists():
        raise SystemExit('Labels are already locked; keep the original experiment intact.')
    labels=read_labels(plan)
    write_json(ROOT/'labels.lock.json',dict(created=datetime.now(timezone.utc).isoformat(),plan_sha256=plan['sha256'],labels_sha256=digest(labels),labels=labels))
    print('Pre-run labels locked. The runner can now produce model/policy answers.')


def run_assessment(use_llm):
    plan=json.loads((ROOT/'plan.json').read_text(encoding='utf-8'))
    if not (ROOT/'labels.lock.json').exists():
        raise SystemExit('Pre-run labels are required. Complete evaluation/real/labels.csv, then run: python real_evaluation.py lock')
    locked=json.loads((ROOT/'labels.lock.json').read_text(encoding='utf-8'))
    unsigned={k:v for k,v in plan.items() if k!='sha256'}
    if digest(unsigned)!=plan['sha256'] or plan['sha256']!=locked['plan_sha256'] or digest(read_labels(plan))!=locked['labels_sha256'] or digest(locked['labels'])!=locked['labels_sha256']:
        raise SystemExit('Selection or pre-run labels changed after locking.')
    out=ROOT/('llm_predictions.json' if use_llm else 'graph_predictions.json')
    if out.exists():raise SystemExit('Prediction file already exists. No silent reruns or cherry-picking.')
    real=RealCases(Store())
    datasets=real.stats()['datasets']
    if not any(d['id']=='gitbugs-spark' and d['revision']==plan['dataset_revision'] for d in datasets):
        raise SystemExit('Graph dataset revision does not match the frozen assessment.')
    results=[]
    for case in plan['cases']:
        started=perf_counter()
        try:
            r=investigate(real,case['report'],use_llm,case['issue_id'])
            results.append(dict(case_id=case['case_id'],latency_ms=round((perf_counter()-started)*1000,2),result=r,error=None))
        except (LLMUnavailable,KeyError,ValueError) as error:
            results.append(dict(case_id=case['case_id'],latency_ms=round((perf_counter()-started)*1000,2),result=None,error=str(error)))
        write_json(out,dict(protocol=plan['protocol'],policy_version=VERSION,
                            caveat='This case set has informed implementation changes; later runs are development diagnostics, not fresh validation.',
                            plan_sha256=plan['sha256'],labels_sha256=locked['labels_sha256'],mode='llm' if use_llm else 'graph',results=results))
    print('Raw predictions saved. Review evidence relevance before reporting human relevance/acceptability.')
    review_path=ROOT/('post_review_'+('llm' if use_llm else 'graph')+'.csv')
    with review_path.open('w',encoding='utf-8',newline='') as file:
        writer=csv.DictWriter(file,fieldnames=['case_id','reviewer','evidence_relevant','step_acceptable','citations_supported','failure_note'])
        writer.writeheader()
        for case in plan['cases']:writer.writerow({'case_id':case['case_id']})


def summarize():
    plan=json.loads((ROOT/'plan.json').read_text(encoding='utf-8'))
    locked=json.loads((ROOT/'labels.lock.json').read_text(encoding='utf-8'))
    labels={r['case_id']:r for r in locked['labels']}
    summaries=[]
    for name in ('graph','llm'):
        path=ROOT/(name+'_predictions.json')
        if not path.exists():continue
        rows=json.loads(path.read_text(encoding='utf-8'))['results'];ok=[r for r in rows if r['result']]
        agreement=sum(r['result']['decision']['next_step'] in labels[r['case_id']]['acceptable_steps'].split(';') for r in ok)
        abstain=[r for r in rows if labels[r['case_id']]['must_abstain']=='yes']
        abstain_ok=sum(bool(r['result']) and r['result']['decision']['next_step']=='request_details' for r in abstain)
        citation_membership=0
        for row in ok:
            r=row['result'];c=r['context'];ids={m['id'] for m in r['matches'][:5]}
            if c:ids|={c['issue']['id']}|{m['id'] for m in c['related'][:4]}|{m['id'] for m in c.get('component_related',[])[:4]}
            if c:ids|={m['id'] for m in c.get('ranked_evidence',[])[:5]}
            citation_membership+=set(r['decision']['evidence_ids'])<=ids
        relevance_covered=[r for r in ok if labels[r['case_id']]['relevant_issue_ids'].strip()]
        hits=sum(bool({m['id'] for m in r['result']['matches'][:5]} & set(labels[r['case_id']]['relevant_issue_ids'].split(';'))) for r in relevance_covered)
        post_path=ROOT/('post_review_'+name+'.csv')
        post=[]
        if post_path.exists():
            with post_path.open(encoding='utf-8-sig',newline='') as source:post=list(csv.DictReader(source))
        if len({r['case_id'] for r in post}) != len(post) or any(r['case_id'] not in labels for r in post):
            raise SystemExit('Post-review IDs must be unique and belong to the frozen cases.')
        judged=[r for r in post if r['reviewer'].strip() and all(r.get(k) in ('yes','no') for k in ('evidence_relevant','step_acceptable','citations_supported'))]
        summaries.append(dict(mode=name,completed=len(ok),attempted=len(rows),step_agreement=agreement,
                              required_abstentions=len(abstain),correct_abstentions=abstain_ok,
                              citation_membership=citation_membership,citation_support='Post-review checks factual source binding only; it does not establish recommendation adequacy or root cause.',
                              original_source_in_top5=sum(any(m['id']==next(c['issue_id'] for c in plan['cases'] if c['case_id']==r['case_id']) for m in r['result']['matches'][:5]) for r in ok),
                              predeclared_relevance_cases=len(relevance_covered),top5_hits_on_judged_cases=hits,
                              postrun_judged=len(judged),postrun_evidence_relevant=sum(r['evidence_relevant']=='yes' for r in judged),
                              postrun_step_acceptable=sum(r['step_acceptable']=='yes' for r in judged),
                              postrun_citations_supported=sum(r['citations_supported']=='yes' for r in judged),
                              postrun_failure_notes=[{'case_id':r['case_id'],'note':r['failure_note']} for r in judged if r['failure_note']],
                              failures=[dict(case_id=r['case_id'],error=r['error'],decision=r['result']['decision'] if r['result'] else None) for r in rows if not r['result'] or r['result']['decision']['next_step'] not in labels[r['case_id']]['acceptable_steps'].split(';')]))
    write_json(ROOT/'summary.json',dict(protocol=plan['protocol'],reviewer_kinds=sorted({r['reviewer_kind'] for r in locked['labels']}),summaries=summaries,
                                     caveat='Known-history study. Predeclared labels are human only if reviewer_kind is human. No independently held-out retrieval or accuracy claim.'))
    print(json.dumps(summaries,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['prepare','lock','run','summarize']);parser.add_argument('--llm',action='store_true');args=parser.parse_args()
    if args.command=='prepare':prepare()
    elif args.command=='lock':lock()
    elif args.command=='run':run_assessment(args.llm)
    else:summarize()
