"""Explainable text mentions, not inferred ownership or dependencies."""
import re

RULE_VERSION = 'component-mentions-v1'
RULES = [
    ('pyspark', 'Python / PySpark', r'\b(?:pyspark|python)\b'),
    ('sql', 'Spark SQL / DataFrames', r'\b(?:sql|dataframes?|catalyst)\b'),
    ('streaming', 'Streaming', r'\b(?:streaming|dstreams?)\b'),
    ('kafka', 'Kafka', r'\bkafka\b'),
    ('hive', 'Hive', r'\bhive\b'),
    ('parquet', 'Parquet', r'\bparquet\b'),
    ('orc', 'ORC', r'\borc\b'),
    ('arrow', 'Arrow', r'\b(?:apache\s+)?arrow\b'),
    ('yarn', 'YARN', r'\byarn\b'),
    ('kubernetes', 'Kubernetes', r'\b(?:kubernetes|k8s)\b'),
    ('hdfs', 'HDFS', r'\bhdfs\b'),
    ('shuffle', 'Shuffle', r'\bshuffle\b'),
    ('scheduler', 'Scheduler', r'\b(?:scheduler|dagscheduler|taskscheduler)\b'),
    ('jdbc', 'JDBC', r'\bjdbc\b'),
    ('mllib', 'MLlib', r'\b(?:mllib|spark\.ml)\b'),
    ('connect', 'Spark Connect', r'\bspark\s+connect\b'),
]
COMPILED = [(cid, name, re.compile(pattern, re.I)) for cid, name, pattern in RULES]


def mentions(row):
    found = []
    for cid, name, pattern in COMPILED:
        for field in ('title', 'description'):
            text = row.get(field, '')
            match = pattern.search(text)
            if match:
                snippet = re.sub(r'\s+', ' ', text[max(0,match.start()-65):match.end()+95]).strip()
                found.append(dict(issue=row['id'], component=cid, name=name, field=field,
                                  matched=match.group(), excerpt=snippet, rule=RULE_VERSION))
                break
    return found


def enrich(store, rows):
    if not any(r[0] == 'Component' for r in store.graph.list_indices().result_set):
        store.write('CREATE INDEX FOR (n:Component) ON (n.id)')
    batch, count = [], 0
    def flush(items):
        store.write('''UNWIND $rows AS row
            MATCH (i:HistoricalIssue {id:row.issue})
            MERGE (c:Component {id:row.component}) SET c.name=row.name
            MERGE (i)-[m:MENTIONS]->(c)
            SET m.excerpt=row.excerpt, m.field=row.field, m.matched=row.matched,
                m.rule=row.rule, m.kind='text_mention' ''', rows=items)
    for row in rows:
        found = mentions(row)
        count += len(found)
        batch.extend(found)
        if len(batch) >= 400:
            flush(batch)
            batch = []
    if batch:
        flush(batch)
    print(f'Component enrichment: {count} source-backed mentions, rule {RULE_VERSION}. No dependency or root-cause edges inferred.')
    return count


if __name__ == '__main__':
    from graph import Store
    from import_real_data import download, records
    enrich(Store(), records(download()))
