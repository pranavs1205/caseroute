"""All domain context and memory lives in FalkorDB. No fallback owner map."""
import os
from datetime import datetime, timezone
from uuid import uuid4

from falkordb import FalkorDB


class Store:
    def __init__(self, name=None):
        self.graph = FalkorDB(
            host=os.getenv('FALKORDB_HOST', '127.0.0.1'),
            port=int(os.getenv('FALKORDB_PORT', '6380')),
            password=os.getenv('FALKORDB_PASSWORD') or None,
            socket_timeout=8,
        ).select_graph(name or os.getenv('FALKORDB_GRAPH', 'caseroute'))

    def read(self, query, **params):
        result = self.graph.ro_query(query, params, timeout=3000)
        keys = [h[1] for h in result.header]
        return [dict(zip(keys, row)) for row in result.result_set]

    def write(self, query, **params):
        return self.graph.query(query, params, timeout=3000).result_set

    def catalog(self):
        return {
            'features': self.read('MATCH (f:Feature) RETURN f.id AS id, f.name AS name ORDER BY name'),
            'services': self.read('MATCH (s:Service) RETURN s.id AS id, s.name AS name ORDER BY name'),
            'teams': self.read('MATCH (t:Team) RETURN t.id AS id, t.name AS name ORDER BY name'),
        }

    def cases(self):
        return self.read('MATCH (c:Case)-[:ABOUT]->(f:Feature) RETURN c.id AS id, c.report AS report, f.name AS feature, c.created AS created ORDER BY created DESC LIMIT 50')

    def create_case(self, feature, report):
        cid = 'CR-' + uuid4().hex[:10].upper()
        rows = self.write('MATCH (f:Feature {id:$feature}) CREATE (c:Case {id:$id, report:$report, created:$now})-[:ABOUT]->(f) RETURN c.id',
                          feature=feature, id=cid, report=report, now=datetime.now(timezone.utc).isoformat())
        if not rows:
            raise ValueError('Unknown feature')
        return cid

    def investigate(self, cid, selected=None):
        cases = self.read('MATCH (c:Case {id:$id})-[:ABOUT]->(f:Feature) RETURN c.report AS report, f.id AS feature_id, f.name AS feature', id=cid)
        if not cases:
            raise KeyError('Case not found')
        case = cases[0]
        owners = self.read('''MATCH (c:Case {id:$id})-[:ABOUT]->(f:Feature)-[:DEPENDS_ON]->(s:Service)-[o:OWNED_BY]->(t:Team)
            RETURN s.id AS service_id, s.name AS service, t.name AS team,
            o.source AS source, o.updated AS updated ORDER BY service, team''', id=cid)
        history = self.read('''MATCH (:Case {id:$id})-[r:TRIED]->(a:Action)
            RETURN a.id AS action_id, a.title AS action, r.outcome AS outcome, r.at AS at, r.note AS note ORDER BY at DESC''', id=cid)
        candidates = self.read('''MATCH (c:Case {id:$id})-[:ABOUT]->(f:Feature)-[:DEPENDS_ON]->(s:Service)<-[:FOR_SERVICE]-(a:Action)-[:SUPPORTED_BY]->(d:Document)
            OPTIONAL MATCH (past:ResolvedCase)-[:ABOUT]->(f), (past)-[:FIXED_BY]->(a)
            RETURN s.id AS service_id, a.id AS id, a.title AS title, a.priority AS priority,
            d.id AS source, d.title AS document, d.excerpt AS excerpt, d.updated AS updated,
            collect(DISTINCT past.title) AS past_cases ORDER BY priority, id''', id=cid)
        service_ids = {o['service_id'] for o in owners}
        if selected and selected not in service_ids:
            raise ValueError('Selected service does not belong to this case')
        ambiguity = len(service_ids) > 1 and not selected
        chosen_owners = [o for o in owners if not selected or o['service_id'] == selected]
        conflict = len({o['team'] for o in chosen_owners}) > 1
        blocked = ambiguity or conflict or not owners
        tried = {h['action_id'] for h in history}
        available = [a for a in candidates if a['id'] not in tried and (not selected or a['service_id'] == selected)]
        available.sort(key=lambda a: (not bool(a['past_cases']), a['priority'], a['id']))
        action = available[0] if available and not blocked else None
        owner = chosen_owners[0] if chosen_owners and not blocked else None
        status = 'needs_service' if ambiguity else 'ownership_conflict' if conflict else 'missing_owner' if not owners else 'ready' if action else 'exhausted'
        warnings = []
        for source in owners + ([action] if action else []):
            try:
                updated = datetime.fromisoformat(source['updated'].replace('Z', '+00:00'))
                if updated.tzinfo is None:
                    updated = updated.replace(tzinfo=timezone.utc)
                if (datetime.now(timezone.utc) - updated).days > 90:
                    warnings.append(f"{source['source']}: source is over 90 days old; confirm it before acting.")
            except (KeyError, ValueError, TypeError):
                warnings.append(f"{source.get('source', 'Ownership')}: source date is missing or invalid.")
        path = [cid, case['feature']] + ([owner['service'], owner['team']] if owner else [])
        draft = (f"To {owner['team']}: investigate {cid} ({case['feature']}). Customer report: {case['report']}\n"
                 f"Suggested check: {action['title']}\nEvidence: {action['source']} — {action['excerpt']}\nHuman review required before execution.") if action else None
        return dict(id=cid, **case, status=status, owners=owners, history=history, action=action,
                    path=path, draft=draft, available_count=len(available), selected_service=selected, warnings=list(dict.fromkeys(warnings)),
                    tools=['resolve_ownership', 'read_attempt_memory', 'find_documented_actions', 'rank_by_past_resolution'])

    def attempt(self, cid, aid, outcome, note, selected=None):
        state = self.investigate(cid, selected)
        if not state['action'] or state['action']['id'] != aid:
            raise ValueError('Action is no longer recommended; refresh this case')
        self.write('''MATCH (c:Case {id:$id}), (a:Action {id:$aid})
            CREATE (c)-[:TRIED {outcome:$outcome, note:$note, at:$now}]->(a)''',
                   id=cid, aid=aid, outcome=outcome, note=note, now=datetime.now(timezone.utc).isoformat())
        return self.investigate(cid, selected)

    def impact(self, service):
        exists = self.read('MATCH (s:Service {id:$id}) RETURN s.name AS name', id=service)
        if not exists:
            raise KeyError('Service not found')
        rows = self.read('''MATCH (f:Feature)-[:DEPENDS_ON]->(s:Service)-[:DEPENDS_ON*0..3]->(target:Service {id:$id})
            MATCH (s)-[:OWNED_BY]->(t:Team)
            OPTIONAL MATCH (c:Case)-[:ABOUT]->(f)
            RETURN DISTINCT f.name AS feature, s.name AS service, t.name AS team, c.id AS case_id ORDER BY feature''', id=service)
        paths = self.read('''MATCH (f:Feature)-[:DEPENDS_ON]->(s:Service)
            MATCH p=(s)-[:DEPENDS_ON*0..3]->(:Service {id:$id})
            RETURN DISTINCT f.name AS feature, [n IN nodes(p) | n.name] AS services ORDER BY feature''', id=service)
        return dict(service=exists[0]['name'], affected=rows, paths=paths, max_service_hops=3, read_only=True)

    def change_owner(self, service, team):
        # Controlled demo mutation: source and timestamp move with the ownership edge.
        rows = self.write('''MATCH (s:Service {id:$service}), (t:Team {id:$team})
            OPTIONAL MATCH (s)-[old:OWNED_BY]->(:Team)
            WITH s,t,collect(old) AS old_edges
            FOREACH (edge IN old_edges | DELETE edge)
            CREATE (s)-[:OWNED_BY {source:'DEMO-OWNERSHIP-CHANGE', updated:$now}]->(t)
            RETURN t.name''', service=service, team=team, now=datetime.now(timezone.utc).isoformat())
        if not rows:
            raise ValueError('Unknown service or team')
        return {'team': rows[0][0]}
