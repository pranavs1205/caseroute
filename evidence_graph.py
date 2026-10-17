"""Source-backed identifiers and degree-discounted, two-hop evidence retrieval.

This is a transparent local shared-neighbor score, not PageRank or a claim of
causality. Source strings are data; no model-generated Cypher is executed.
"""
import re

RULE = 'technical-identifiers-v2'
IDENTIFIER = re.compile(r'\b[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*\b')
STACK = re.compile(r'^\s*(?:at\s+|File\s+"|\.\.\.\s*\d+)', re.I)


def stack_line(line):
    return bool(STACK.match(line) or re.search(r'(?:^|\s)at\s+\S+\([^)]*\)', line)
                or re.search(r'\bFile "[^"]+", line \d+', line))


def identifiers(row):
    found = {}
    for field in ('title', 'description'):
        text = (row.get(field) or '')[:12000]
        for line in text.splitlines():
            if stack_line(line):
                continue
            for match in IDENTIFIER.finditer(line):
                token = match.group()
                if len(token) < 5 or len(token) > 160:
                    continue
                if not ('.' in token or '_' in token or re.search(r'[a-z][A-Z]', token)):
                    continue
                # Package prefixes alone are broad infrastructure, not mechanisms.
                if token in ('org.apache.spark', 'java.lang', 'scala.collection'):
                    continue
                value = '.'.join(token.split('.')[-2:])
                key = value.lower()
                if key in found:
                    continue
                found[key] = dict(issue=row['id'], id=key, value=value, matched=token,
                                  field=field, excerpt=line[max(0,match.start()-80):match.end()+120].strip(), rule=RULE,
                                  weight=3.0 if field == 'title' else 1.0)
    # Deterministic bound: prioritize titles, named exceptions and test suites.
    return sorted(found.values(), key=lambda x: (
        x['field'] != 'title', not bool(re.search(r'Exception|Error|Suite|Provider', x['value'])), x['id']))[:24]


def enrich(store, rows):
    if not any(r[0] == 'EvidenceSignal' for r in store.graph.list_indices().result_set):
        store.write('CREATE INDEX FOR (s:EvidenceSignal) ON (s.id)')
    batch, count = [], 0
    def flush(items):
        # Replace this derived index per issue, preserving source and reviews.
        # Necessary when a rule revision removes previously indexed stack noise.
        store.write('''UNWIND $ids AS iid MATCH (:HistoricalIssue {id:iid})-[e:HAS_SIGNAL]->()
            DELETE e''', ids=list({r['issue'] for r in items}))
        store.write('''UNWIND $rows AS row
            MATCH (i:HistoricalIssue {id:row.issue})
            MERGE (s:EvidenceSignal {id:row.id}) SET s.value=row.value
            MERGE (i)-[e:HAS_SIGNAL]->(s)
            SET e.matched=row.matched, e.field=row.field, e.excerpt=row.excerpt,
                e.rule=row.rule, e.weight=row.weight''', rows=items)
    for row in rows:
        signals = identifiers(row)
        count += len(signals)
        if not signals:
            store.write('MATCH (:HistoricalIssue {id:$id})-[e:HAS_SIGNAL]->() DELETE e', id=row['id'])
        batch.extend(signals)
        if len(batch) >= 400:
            flush(batch); batch = []
    if batch:
        flush(batch)
    store.write('MATCH (s:EvidenceSignal) WHERE NOT (s)<-[:HAS_SIGNAL]-() DELETE s')
    store.write('''MATCH (s:EvidenceSignal)<-[:HAS_SIGNAL]-(i:HistoricalIssue)
        WITH s, count(i) AS degree SET s.degree=degree''')
    store.write('''MATCH (c:Component)<-[:MENTIONS]-(i:HistoricalIssue)
        WITH c, count(i) AS degree SET c.degree=degree''')
    return count


def ranked_neighbors(real, iid, trace=None):
    return real.query(trace, 'rank_technical_evidence',
        'Rank two-hop issue → exact technical identifier ← issue paths. Divide contributions by signal degree to discount hubs; exclude the source itself.', '''
        MATCH (i:HistoricalIssue {id:$id})-[a:HAS_SIGNAL]->(s:EvidenceSignal)
        WHERE s.degree <= 500 AND s.degree > 1
        WITH i, a, s
        MATCH (s)<-[b:HAS_SIGNAL]-(other:HistoricalIssue)
        WHERE other.id <> i.id
        WITH other,s,a,b,a.weight*b.weight/toFloat(s.degree) AS contribution
        ORDER BY contribution DESC
        WITH other, sum(contribution) AS graph_score,
            collect({signal:s.value, degree:s.degree, source_excerpt:a.excerpt,
                candidate_excerpt:b.excerpt, contribution:contribution}) AS paths
        RETURN other.id AS id, other.title AS title, other.resolution AS resolution,
            other.url AS url, substring(other.description,0,900) AS description,
            graph_score, paths ORDER BY graph_score DESC, id ASC LIMIT 8''', id=iid)


if __name__ == '__main__':
    from graph import Store
    from import_real_data import download, records
    print('Technical identifier links:', enrich(Store(), records(download())))
