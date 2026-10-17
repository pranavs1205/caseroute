"""Actual graph projections for the interactive canvas. No inferred dependencies."""
from time import perf_counter


class Landscape:
    def __init__(self, real):
        self.real = real
        self.store = real.store

    def examples(self):
        return self.store.read('''MATCH (i:HistoricalIssue)-[m:MENTIONS]->(c:Component)
            WITH i, collect(DISTINCT c.name) AS components,
              sum(CASE WHEN m.field='title' THEN 1 ELSE 0 END) AS title_mentions
            WHERE size(components)>=3 AND title_mentions>=2
            RETURN i.id AS id, i.title AS title, i.resolution AS resolution,
                components, title_mentions
            ORDER BY title_mentions DESC, id DESC LIMIT 6''')

    def projection(self, iid=None):
        started = perf_counter()
        trace = []
        context = self.real.context(iid, trace) if iid else None
        ids = None
        if context:
            ids = list(dict.fromkeys([iid] + [r['id'] for r in context['component_related']] + [r['id'] for r in context['related']]))
        issue_query = '''MATCH (i:HistoricalIssue) RETURN i.id AS id, i.title AS label,
            'issue' AS kind, i.resolution AS resolution, i.url AS url'''
        edge_query = '''MATCH (i:HistoricalIssue)-[r]->(n)
            WHERE type(r) IN ['MENTIONS','AFFECTS','IN_PROJECT','SOURCED_FROM']
            RETURN i.id AS source, n.id AS target, type(r) AS kind'''
        if ids is not None:
            issue_query = '''UNWIND $ids AS iid MATCH (i:HistoricalIssue {id:iid})
                RETURN i.id AS id, i.title AS label, 'issue' AS kind, i.resolution AS resolution, i.url AS url'''
            edge_query = '''UNWIND $ids AS iid MATCH (i:HistoricalIssue {id:iid})-[r]->(n)
                WHERE type(r) IN ['MENTIONS','AFFECTS','IN_PROJECT','SOURCED_FROM']
                RETURN i.id AS source, n.id AS target, type(r) AS kind,
                    r.excerpt AS excerpt, r.field AS field, r.rule AS rule'''
        params = {'ids':ids} if ids else {}
        if iid:
            nodes = self.real.query(trace, 'load_issue_nodes', 'Load all issue nodes in the requested graph scope.', issue_query, **params)
            edges = self.real.query(trace, 'load_issue_relationships', 'Load actual stored relationships; component links mean text mentions.', edge_query, **params)
        else:
            # One collection row avoids the database's per-row result cap and
            # repeated sorting/paging of this bounded, 20k-issue corpus. Verify
            # the collection lengths against independent counts below.
            def collection(query, name):
                tick=perf_counter()
                items=self.store.read(query)[0]['items']
                trace.append(dict(kind='graph', tool=name, purpose='Load the complete bounded projection as a collection row, bypassing the per-row result cap.',
                                  cypher=query, parameters={}, rows=1, records=len(items), preview=items[:3],
                                  duration_ms=round((perf_counter()-tick)*1000,2), outcome=f'Returned one collection row containing {len(items)} graph records.'))
                return items
            node_items=collection('MATCH (i:HistoricalIssue) RETURN collect([i.id,i.title,i.resolution,i.url]) AS items', 'load_all_issue_nodes')
            edge_items=collection("MATCH (i:HistoricalIssue)-[r]->(n) WHERE type(r) IN ['MENTIONS','AFFECTS','IN_PROJECT','SOURCED_FROM'] RETURN collect([i.id,n.id,type(r)]) AS items", 'load_all_relationships')
            nodes=[dict(id=r[0],label=r[1],resolution=r[2],url=r[3],kind='issue') for r in node_items]
            edges=[dict(source=r[0],target=r[1],kind=r[2]) for r in edge_items]
            expected = self.store.read('MATCH (i:HistoricalIssue) RETURN count(i) AS n')[0]['n']
            expected_edges = self.store.read("MATCH (:HistoricalIssue)-[r]->() WHERE type(r) IN ['MENTIONS','AFFECTS','IN_PROJECT','SOURCED_FROM'] RETURN count(r) AS n")[0]['n']
            if len(nodes)!=expected or len(edges)!=expected_edges:
                raise ValueError('Graph changed during loading or a page was truncated; retry the full graph.')
        other_nodes = self.store.read('''MATCH (n) WHERE n:Component OR n:Version OR n:Project OR n:Dataset
            RETURN n.id AS id, n.name AS label, labels(n)[0] AS label_type''')
        target_ids = {r['target'] for r in edges}
        kinds = {'Component':'component', 'Version':'version', 'Project':'project', 'Dataset':'source'}
        nodes.extend(dict(id=n['id'], label=n['label'], kind=kinds[n['label_type']]) for n in other_nodes if not iid or n['id'] in target_ids)
        node_ids = {n['id'] for n in nodes}
        hierarchy = self.store.read('''MATCH (n)-[r]->(p) WHERE type(r) IN ['VERSION_OF','DOCUMENTED_IN']
            RETURN n.id AS source, p.id AS target, type(r) AS kind''')
        edges.extend(r for r in hierarchy if r['source'] in node_ids and r['target'] in node_ids)
        if context:
            for review in context['memory']:
                nodes.append(dict(id=review['id'], kind='review', label=review['outcome'], note=review['note']))
                edges.append(dict(source=review['id'], target=iid, kind='BASED_ON'))
        return dict(scope='investigation' if iid else 'corpus', seed=iid, nodes=nodes, edges=edges, context=context,
                    trace=trace, query_ms=round((perf_counter()-started)*1000,2),
                    issue_count=sum(n['kind']=='issue' for n in nodes),
                    scope_note='All real historical issues, affected versions, component mentions and source/project relationships. Fictional lab and past run records are separate.' if not iid else 'Selected issue, up to 8 component-intersection leads, up to 8 shared-version leads, their relationships and saved reviews.',
                    edge_semantics='MENTIONS is rule-extracted from a source excerpt. It does not assert a dependency, diagnosis or verified fix.')
