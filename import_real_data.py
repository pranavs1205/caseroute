"""Bounded, revision-pinned import of genuine historical Apache Spark reports."""
import argparse
import csv
import hashlib
import json
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from graph import Store

REVISION = 'eadf2d6794990a1aaa26d0ae15391f29f8969301'
SOURCE = f'https://raw.githubusercontent.com/av9ash/gitbugs/{REVISION}/spark/spark_bugs.csv'
EXPECTED_BYTES = 18665594
EXPECTED_SHA256 = '34c18f07ab9877dfe15471d8356eb017b7658a87f0e1a20bf60043659ff1af02'
MAX_BYTES = 25_000_000
RAW = Path(__file__).parent / 'data' / 'raw' / 'spark_bugs.csv'
MANIFEST = Path(__file__).parent / 'data' / 'manifest.json'


def download():
    RAW.parent.mkdir(parents=True, exist_ok=True)
    if RAW.exists() and RAW.stat().st_size == EXPECTED_BYTES:
        if hashlib.sha256(RAW.read_bytes()).hexdigest() != EXPECTED_SHA256:
            raise ValueError('Cached CSV checksum mismatch; remove the corrupted cache and retry.')
        return RAW
    partial = RAW.with_suffix('.partial')
    try:
        request = urllib.request.Request(SOURCE, headers={'User-Agent': 'CaseRoute research prototype'})
        with urllib.request.urlopen(request, timeout=45) as response, partial.open('wb') as output:
            if int(response.headers.get('Content-Length', 0)) > MAX_BYTES:
                raise ValueError('Dataset exceeds the 25 MB download cap')
            total = 0
            while chunk := response.read(64 * 1024):
                total += len(chunk)
                if total > MAX_BYTES:
                    raise ValueError('Dataset exceeds the 25 MB download cap')
                output.write(chunk)
        if total != EXPECTED_BYTES:
            raise ValueError(f'Pinned file size mismatch: {total}')
        if hashlib.sha256(partial.read_bytes()).hexdigest() != EXPECTED_SHA256:
            raise ValueError('Downloaded CSV checksum mismatch')
        partial.replace(RAW)
    finally:
        partial.unlink(missing_ok=True)
    return RAW


def records(path):
    csv.field_size_limit(5_000_000)
    with path.open(encoding='utf-8-sig', newline='') as file:
        for number, raw in enumerate(csv.DictReader(file), start=2):
            issue_id = raw['Issue id'].strip()
            if not issue_id.isdigit():
                raise ValueError(f'Unexpected issue ID on CSV record {number}')
            # CSV dates have no timezone: preserve the original text without inventing one.
            versions = sorted(set(v.strip() for v in raw['Affects Version/s'].split(',') if v.strip()))
            title = raw['Summary'].strip()
            description = raw['Description'].strip()
            yield dict(id='spark-' + issue_id, external_id=issue_id, title=title,
                       description=description, search_text=(title + '\n' + description).lower(),
                       status=raw['Status'].strip(), priority=raw['Priority'].strip(),
                       resolution=raw['Resolution'].strip(), created=raw['Created'].strip(),
                       resolved=raw['Resolved'].strip(), versions=versions, record=number,
                       url='https://issues.apache.org/jira/secure/ViewIssue.jspa?id=' + issue_id)


def load(store, path):
    store.write('''MERGE (d:Dataset {id:'gitbugs-spark'})
        SET d.name='GitBugs / Apache Spark', d.url=$url, d.revision=$revision,
            d.license='CC BY 4.0', d.author='Avinash Patil', d.kind='real_historical'
        MERGE (p:Project {id:'apache-spark'}) SET p.name='Apache Spark'
        MERGE (p)-[:DOCUMENTED_IN]->(d)''', url=SOURCE, revision=REVISION)
    # Indexes keep the per-batch MERGEs and later ID lookups bounded.
    for label in ('HistoricalIssue', 'Version'):
        indices = store.graph.list_indices().result_set
        if not any(i[0] == label for i in indices):
            store.write(f'CREATE INDEX FOR (n:{label}) ON (n.id)')
    batch, count, seen = [], 0, set()
    outcomes, versions_count = Counter(), Counter()

    def flush(rows):
        store.write('''UNWIND $rows AS row
            MERGE (i:HistoricalIssue {id:row.id})
            SET i.external_id=row.external_id, i.title=row.title, i.description=row.description,
                i.search_text=row.search_text, i.status=row.status, i.priority=row.priority,
                i.resolution=row.resolution, i.created=row.created, i.resolved=row.resolved,
                i.url=row.url, i.record=row.record
            WITH i MATCH (d:Dataset {id:'gitbugs-spark'}), (p:Project {id:'apache-spark'})
            MERGE (i)-[:SOURCED_FROM]->(d) MERGE (i)-[:IN_PROJECT]->(p)''', rows=rows)
        version_rows = [dict(id=r['id'], version=v, vid='spark:' + v) for r in rows for v in r['versions']]
        if version_rows:
            store.write('''UNWIND $rows AS row
                MATCH (i:HistoricalIssue {id:row.id}), (p:Project {id:'apache-spark'})
                MERGE (v:Version {id:row.vid}) SET v.name=row.version
                MERGE (i)-[:AFFECTS]->(v) MERGE (v)-[:VERSION_OF]->(p)''', rows=version_rows)

    for row in records(path):
        if row['id'] in seen:
            raise ValueError('Duplicate issue ID in source: ' + row['id'])
        seen.add(row['id'])
        count += 1
        outcomes[row['resolution'] or 'unrecorded'] += 1
        versions_count.update(row['versions'])
        batch.append(row)
        if len(batch) == 200:
            flush(batch)
            batch = []
    if batch:
        flush(batch)
    store.write('MATCH (d:Dataset {id:\'gitbugs-spark\'}) SET d.rows=$rows, d.imported=$now, d.bytes=$size',
                rows=count, now=datetime.now(timezone.utc).isoformat(), size=path.stat().st_size)
    manifest = dict(dataset='GitBugs / Apache Spark', revision=REVISION, source=SOURCE,
                    publisher='https://github.com/av9ash/gitbugs', paper='https://arxiv.org/abs/2504.09651',
                    author='Avinash Patil', license='CC BY 4.0', license_url='https://creativecommons.org/licenses/by/4.0/',
                    bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                    rows=count, unique_versions=len(versions_count), resolutions=dict(outcomes),
                    imported_at=datetime.now(timezone.utc).isoformat(),
                    transformations=['Preserved original dates without assuming a timezone.',
                                     'Split comma-delimited affected versions into Version nodes.',
                                     'Added dataset provenance and constructed JIRA URLs from internal numeric issue IDs.',
                                     'No owner, root cause, fix procedure, duplicate target, or service dependency was inferred.'])
    MANIFEST.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--download-only', action='store_true')
    args = parser.parse_args()
    path = download()
    if args.download_only:
        print(path, path.stat().st_size)
    else:
        load(Store(), path)
        from components import enrich
        enrich(Store(), records(path))
