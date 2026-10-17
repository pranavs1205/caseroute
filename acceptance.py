"""Windows/local setup gate. Never resets the user's demo graph or volume."""
import argparse
import contextlib
import io
import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from components import enrich
from graph import Store
from import_real_data import download, load, records
from landscape import Landscape
from real_cases import RealCases
from llm import investigate
from seed import seed
from evidence_graph import enrich as enrich_evidence


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',default='artifacts/setup-check.json')
    args=parser.parse_args()
    subprocess.run(['docker','compose','config','--quiet'],check=True)
    version=subprocess.run(['docker','version','--format','{{.Server.Version}}'],check=True,capture_output=True,text=True).stdout.strip()
    name='caseroute_setup_check_'+uuid4().hex
    store=Store(name)
    result=dict(created=datetime.now(timezone.utc).isoformat(),python=platform.python_version(),platform=platform.system(),
                docker_server=version,graph=name,checks=[],passed=False)
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            seed(store)
            source=download()
            load(store,source,manifest_path=None)
            enriched=enrich(store,records(source))
            signal_links=enrich_evidence(store,records(source))
        real=RealCases(store)
        assert real.stats()['issues']==20275
        assert real.stats()['versions']==68
        result['checks'].append('Fresh graph: full pinned CSV imported; 20,275 reports / 68 versions')
        assert enriched==13909
        result['checks'].append('Fresh component enrichment: 13,909 excerpt-backed links')
        assert signal_links > 0
        assert store.read('MATCH ()-[e:HAS_SIGNAL]->() WHERE NOT e.excerpt CONTAINS e.matched RETURN count(e) AS n')[0]['n']==0
        result['checks'].append(f'Fresh technical-identifier index: {signal_links} excerpt-backed links; no unsupported excerpts')
        cid=store.create_case('discounts','Clean setup gate: checkout fails with discount')
        store.attempt(cid,'pricing-cache','failed','Clean gate: cache versions match')
        assert Store(name).investigate(cid)['action']['id']=='pricing-rule'
        result['checks'].append('Fresh-client attempt persistence and a different next check')
        run=investigate(real,'Error in writing a pyspark streaming dataframe created from Kafka source to a csv file',False,'spark-13289604')
        assert run['decision']['next_step']=='investigate_component_boundary'
        assert len(run['context']['components'])==4
        real.review('spark-13289604','needs_more_info','Setup gate: current environment and reproduction were not provided')
        changed=investigate(RealCases(Store(name)),run['report'],False,'spark-13289604')
        assert changed['decision']['next_step']=='request_details'
        assert real.run(changed['id'])['decision']==changed['decision']
        result['checks'].append('Real four-component case, changed decision after review, saved-run reload')
        graph=Landscape(real).projection()
        assert graph['issue_count']==20275 and len(graph['nodes'])==20361 and len(graph['edges'])==74803
        result['full_graph_query_ms']=graph['query_ms']
        result['checks'].append('Full real projection: independent count checks pass')
        result['passed']=True
    finally:
        assert name.startswith('caseroute_setup_check_') and store.graph.name==name
        store.graph.delete()
        result['temporary_graph_deleted']=True
        destination=Path(args.output);destination.parent.mkdir(parents=True,exist_ok=True)
        destination.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
