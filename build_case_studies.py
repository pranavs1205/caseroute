"""Capture observed demo behavior; human assessment fields remain explicitly pending."""
import contextlib
import io
import json
from pathlib import Path
from uuid import uuid4

from components import enrich
from graph import Store
from import_real_data import download, load, records
from llm import investigate
from real_cases import RealCases

CASES=[('multi-component','spark-13289604'),('straightforward','spark-13524752'),('insufficient-source','spark-13522896')]


def main():
    root=Path('case_studies');root.mkdir(exist_ok=True)
    plan=json.loads(Path('evaluation/real/plan.json').read_text(encoding='utf-8'))
    assert not {iid for _,iid in CASES}&{r['issue_id'] for r in plan['cases']},'Demo cases must be separate from the assessment.'
    name='caseroute_case_studies_'+uuid4().hex
    store=Store(name)
    try:
        source=download()
        with contextlib.redirect_stdout(io.StringIO()):
            load(store,source,manifest_path=None);enrich(store,records(source))
        real=RealCases(store)
        for category,iid in CASES:
            context=real.context(iid)
            report=context['issue']['title']
            initial=investigate(real,report,False,iid)
            note='Case-study review: current environment and reproduction details are not supplied; request them before reusing this lead.'
            real.review(iid,'needs_more_info',note)
            after=investigate(RealCases(Store(name)),report,False,iid)
            assert after['decision']['next_step']=='request_details'
            assert real.run(after['id'])['decision']==after['decision']
            issue=context['issue']
            record=dict(category=category,mode='graph_only',source=issue,versions=context['versions'],components=context['components'],
                        version_paths=[dict(from_issue=iid,version=v['version'],project=v['project']) for v in context['versions']],
                        component_leads=context['component_related'],version_leads=context['related'],
                        initial_decision=initial['decision'],review=dict(outcome='needs_more_info',note=note),
                        reloaded_decision=after['decision'],initial_trace=initial['trace'],after_trace=after['trace'],
                        human_assessment=dict(status='pending',evidence_relevant=None,step_acceptable=None,missing_information=None),
                        interpretation='Observed application behavior, not independent human approval or a verified fix.')
            (root/(category+'.json')).write_text(json.dumps(record,indent=2),encoding='utf-8')
            excerpt=issue['description'][:900] or '[No description recorded]'
            text=f'''# {category.replace('-', ' ').title()}: {iid}

**Report:** {issue['title']}
**Source:** {issue['url']} — GitBugs / Apache Spark, Avinash Patil, CC BY 4.0.
**Source record:** {issue['record']}; pinned revision `{issue['revision']}`.
**Recorded outcome:** {issue['resolution'] or 'unrecorded'} (a source label, not a verified fix).

## Problem presented

{report}

## Source excerpt

```text
{excerpt}
```

## Graph evidence

- Affected versions: {', '.join(v['version'] for v in context['versions']) or 'none recorded'}.
- Component mentions: {', '.join(c['name'] for c in context['components']) or 'none detected'}.
- Stored paths: `Issue -AFFECTS-> Version <-AFFECTS- OtherIssue`; `Issue -MENTIONS-> Component <-MENTIONS- OtherIssue`.
- Returned leads: {len(context['related'])} shared-version reports; {len(context['component_related'])} component-intersection reports. Excerpts and exact IDs are in the JSON companion.

## Observed decision and memory effect

Graph-only policy initially selected **{initial['decision']['next_step']}**:

> {initial['decision']['action']}

A clearly marked case-study review recorded `needs_more_info`. A new graph client then selected **{after['decision']['next_step']}**. Reloading the saved run returned the same decision. Historical source status was not changed.

## Human assessment — pending

Reviewer: —
Was the evidence relevant? —
Was the proposed step reasonable? —
What was missing? —

These are observed executions, not an independent quality score. This case is excluded from the frozen 20-case assessment.
'''
            if category=='insufficient-source':
                text+='\n**Observed limitation:** the description is empty. The policy still proposes an environment check from metadata instead of immediately abstaining. A reviewer should assess whether that is acceptable; it does not establish a diagnosis. This limitation is preserved rather than counted as success.\n'
            (root/(category+'.md')).write_text(text,encoding='utf-8')
        print('Captured three real-case studies and persisted-memory effects; independent human assessments remain pending.')
    finally:
        assert store.graph.name==name and name.startswith('caseroute_case_studies_')
        store.graph.delete()


if __name__=='__main__':
    main()
