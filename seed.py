"""Idempotent fictional fixture. Never resets case memory."""
from graph import Store


def seed(store):
    for tid, name in [('commerce', 'Commerce Engineering'), ('growth', 'Growth Platform'), ('platform', 'Platform Reliability')]:
        store.write('MERGE (t:Team {id:$id}) SET t.name=$name', id=tid, name=name)
    for sid, name, team in [('pricing', 'Pricing API', 'commerce'), ('checkout', 'Checkout', 'commerce'), ('campaigns', 'Campaigns', 'growth')]:
        store.write('''MERGE (s:Service {id:$id}) SET s.name=$name
            WITH s MATCH (t:Team {id:$team})
            WITH s,t WHERE NOT (s)-[:OWNED_BY]->() CREATE (s)-[:OWNED_BY {source:'OWNERS-2026-10', updated:'2026-10-15'}]->(t)''', id=sid, name=name, team=team)
    for fid, name, services in [('discounts', 'Discount codes', ['pricing']), ('payment', 'Payment checkout', ['checkout']), ('campaign', 'Campaign checkout', ['checkout', 'campaigns'])]:
        store.write('MERGE (f:Feature {id:$id}) SET f.name=$name', id=fid, name=name)
        for sid in services:
            store.write('MATCH (f:Feature {id:$fid}), (s:Service {id:$sid}) MERGE (f)-[:DEPENDS_ON]->(s)', fid=fid, sid=sid)
    for downstream, upstream in [('checkout', 'pricing'), ('campaigns', 'checkout')]:
        store.write('MATCH (s:Service {id:$s}), (u:Service {id:$u}) MERGE (s)-[:DEPENDS_ON]->(u)', s=downstream, u=upstream)
    actions = [
        ('pricing-cache', 'Compare discount cache version with the active price book', 'pricing', 'RUN-101', 'Discount cache recovery', 'Read the cache version and active price-book revision. If they differ, request approval for a cache refresh.', 1),
        ('pricing-rule', 'Inspect discount eligibility rules for the affected cart', 'pricing', 'RUN-102', 'Discount eligibility checks', 'Compare cart currency, campaign window and minimum subtotal with the active discount rule. Do not change production rules.', 2),
        ('checkout-trace', 'Trace the checkout request to its pricing response', 'checkout', 'RUN-201', 'Checkout failure triage', 'Use the request correlation ID to inspect pricing response status and timeout duration.', 1),
        ('checkout-health', 'Check checkout dependency health and error rate', 'checkout', 'RUN-202', 'Checkout health', 'Review dependency health and the recent checkout error rate before proposing a mitigation.', 2),
        ('campaign-window', 'Verify campaign activation and checkout linkage', 'campaigns', 'RUN-301', 'Campaign activation', 'Inspect campaign activation time and the linked checkout configuration.', 1),
    ]
    for aid, title, sid, doc, dtitle, excerpt, priority in actions:
        store.write('''MERGE (a:Action {id:$id}) SET a.title=$title, a.priority=$priority
            MERGE (d:Document {id:$doc}) SET d.title=$dtitle, d.excerpt=$excerpt, d.updated='2026-10-15'
            WITH a,d MATCH (s:Service {id:$sid}) MERGE (a)-[:FOR_SERVICE]->(s) MERGE (a)-[:SUPPORTED_BY]->(d)''',
                    id=aid, title=title, sid=sid, doc=doc, dtitle=dtitle, excerpt=excerpt, priority=priority)
    store.write('''MERGE (p:ResolvedCase {id:'PAST-42'}) SET p.title='Discount failure after price-book release'
        WITH p MATCH (f:Feature {id:'discounts'}), (a:Action {id:'pricing-cache'})
        MERGE (p)-[:ABOUT]->(f) MERGE (p)-[:FIXED_BY]->(a)''')


if __name__ == '__main__':
    seed(Store())
    print('Synthetic graph seeded. Existing cases and ownership preserved.')
