"""Real historical evidence, kept distinct from the fictional ownership fixture."""
import json
import re
from datetime import datetime, timezone
from time import perf_counter
from uuid import uuid4


STOPWORDS = set('a an and are as at be by can could do does for from has have i in is it my of on or our please the this to was we when with works not after'.split())


def terms_for(text):
    return list(dict.fromkeys(w for w in re.findall(r'[a-z0-9_.]+', text.lower()) if len(w) > 2 and w not in STOPWORDS))[:8]


class RealCases:
    def __init__(self, store):
        self.store = store

    def query(self, trace, name, purpose, query, **params):
        start = perf_counter()
        rows = self.store.read(query, **params)
        if trace is not None:
            trace.append(dict(kind='graph', tool=name, purpose=purpose, cypher=query.strip(),
                              parameters=params, rows=len(rows), duration_ms=round((perf_counter()-start)*1000, 2),
                              preview=[{k: v[:1200] if isinstance(v, str) else v for k, v in row.items()} for row in rows[:3]],
                              outcome=f'Returned {len(rows)} evidence record(s).'))
        return rows

    def stats(self):
        datasets = self.store.read('MATCH (d:Dataset) RETURN d.id AS id, d.name AS name, d.rows AS rows, d.bytes AS bytes, d.url AS url, d.revision AS revision, d.license AS license, d.author AS author, d.imported AS imported')
        counts = self.store.read('MATCH (i:HistoricalIssue) RETURN count(i) AS issues')
        versions = self.store.read('MATCH (v:Version) RETURN count(v) AS versions')
        return dict(datasets=datasets, issues=counts[0]['issues'], versions=versions[0]['versions'],
                    caveat='Historical source snapshot. Shared versions do not establish duplicates or root cause. No owners or fix procedures are present in this CSV.')

    def search(self, text='', version=None, trace=None):
        terms = terms_for(text)
        return self.query(trace, 'search_historical_issues', 'Find source reports matching the supplied symptom and optional affected version.', '''
            MATCH (i:HistoricalIssue)
            WHERE ($empty OR any(term IN $terms WHERE i.search_text CONTAINS term))
              AND ($version = '' OR (i)-[:AFFECTS]->(:Version {name:$version}))
            WITH i, reduce(score=0, term IN $terms | score + CASE WHEN toLower(i.title) CONTAINS term THEN 4 WHEN i.search_text CONTAINS term THEN 1 ELSE 0 END) AS score
            RETURN i.id AS id, i.title AS title, i.priority AS priority, i.status AS status,
                i.resolution AS resolution, i.url AS url, i.created AS created, score
            ORDER BY score DESC, id DESC LIMIT 20''', terms=terms, empty=not bool(terms), version=version or '')

    def context(self, iid, trace=None):
        issues = self.query(trace, 'read_issue_source', 'Read the selected historical issue and its immutable CSV provenance.', '''
            MATCH (i:HistoricalIssue {id:$id})-[:SOURCED_FROM]->(d:Dataset)
            MATCH (i)-[:IN_PROJECT]->(p:Project)
            RETURN i.id AS id, i.title AS title, i.description AS description, i.status AS status,
              i.priority AS priority, i.resolution AS resolution, i.created AS created, i.resolved AS resolved,
              i.url AS url, i.record AS record, p.name AS project,
              d.url AS dataset_url, d.revision AS revision, d.license AS license''', id=iid)
        if not issues:
            raise KeyError('Historical issue not found')
        versions = self.query(trace, 'follow_affected_versions', 'Follow issue → affected version → project, using relationships imported from the CSV.', '''
            MATCH (:HistoricalIssue {id:$id})-[:AFFECTS]->(v:Version)-[:VERSION_OF]->(p:Project)
            RETURN v.name AS version, p.name AS project ORDER BY version''', id=iid)
        related = self.query(trace, 'find_shared_version_reports', 'Follow two hops to other reports affecting the same version. This is context, not proof of a common cause.', '''
            MATCH (i:HistoricalIssue {id:$id})-[:AFFECTS]->(v:Version)<-[:AFFECTS]-(other:HistoricalIssue)
            WHERE other.id <> i.id
            RETURN other.id AS id, other.title AS title, other.resolution AS resolution,
                other.url AS url, collect(DISTINCT v.name) AS shared_versions
            ORDER BY id DESC LIMIT 8''', id=iid)
        memory = self.query(trace, 'read_review_memory', 'Recall this app’s previous human reviews, separate from the historical source status.', '''
            MATCH (r:Review)-[:BASED_ON]->(:HistoricalIssue {id:$id})
            RETURN r.id AS id, r.note AS note, r.outcome AS outcome, r.created AS created ORDER BY created DESC LIMIT 20''', id=iid)
        components = self.query(trace, 'follow_component_mentions', 'Follow source-backed mentions of software components; inspect the supporting excerpt for each link.', '''
            MATCH (:HistoricalIssue {id:$id})-[m:MENTIONS]->(c:Component)
            RETURN c.id AS id, c.name AS name, m.excerpt AS excerpt, m.field AS field,
                m.matched AS matched, m.rule AS rule ORDER BY name''', id=iid)
        component_related = self.query(trace, 'find_component_intersections', 'Find reports that mention the same combination of components, beyond shared affected versions.', '''
            MATCH (i:HistoricalIssue {id:$id})-[:MENTIONS]->(c:Component)<-[:MENTIONS]-(other:HistoricalIssue)
            WHERE i.id <> other.id
            WITH other, collect(DISTINCT c.name) AS shared_components
            WHERE size(shared_components) >= 2
            RETURN other.id AS id, other.title AS title, other.resolution AS resolution,
                other.url AS url, shared_components
            ORDER BY size(shared_components) DESC, id DESC LIMIT 8''', id=iid)
        return dict(issue=issues[0], versions=versions, related=related, memory=memory,
                    components=components, component_related=component_related,
                    warnings=['These reports are historical. Confirm applicability to the current environment.',
                              'Recorded resolution is a status label; the CSV does not provide a verified fix procedure.',
                              'Shared-version links are not duplicate or dependency assertions.'])

    def review(self, iid, outcome, note):
        if not self.store.read('MATCH (i:HistoricalIssue {id:$id}) RETURN i.id AS id', id=iid):
            raise KeyError('Historical issue not found')
        rid = 'REVIEW-' + uuid4().hex[:10]
        self.store.write('''MATCH (i:HistoricalIssue {id:$id})
            CREATE (r:Review {id:$rid, outcome:$outcome, note:$note, created:$now})-[:BASED_ON]->(i)''',
                         id=iid, rid=rid, outcome=outcome, note=note, now=datetime.now(timezone.utc).isoformat())
        return self.context(iid)

    def save_run(self, report, mode, trace, decision, issue_id=None, context=None, matches=None):
        rid = 'RUN-' + uuid4().hex[:12]
        self.store.write('''CREATE (r:InvestigationRun {id:$id, report:$report, mode:$mode,
            trace:$trace, decision:$decision, context:$context, matches:$matches, created:$now})''',
                         id=rid, report=report, mode=mode, trace=json.dumps(trace),
                         decision=json.dumps(decision), context=json.dumps(context), matches=json.dumps(matches or []),
                         now=datetime.now(timezone.utc).isoformat())
        if issue_id:
            self.store.write('MATCH (r:InvestigationRun {id:$id}), (i:HistoricalIssue {id:$issue}) MERGE (r)-[:EXAMINED]->(i)', id=rid, issue=issue_id)
        return rid

    def runs(self):
        return self.store.read('MATCH (r:InvestigationRun) RETURN r.id AS id, r.report AS report, r.mode AS mode, r.created AS created ORDER BY created DESC LIMIT 20')

    def run(self, rid):
        rows = self.store.read('MATCH (r:InvestigationRun {id:$id}) RETURN r.id AS id, r.report AS report, r.mode AS mode, r.trace AS trace, r.decision AS decision, r.created AS created, r.context AS context, r.matches AS matches', id=rid)
        if not rows:
            raise KeyError('Investigation run not found')
        result = rows[0]
        result['trace'] = json.loads(result['trace'])
        result['decision'] = json.loads(result['decision'])
        result['context'] = json.loads(result['context']) if result['context'] else None
        result['matches'] = json.loads(result['matches']) if result['matches'] else []
        return result
