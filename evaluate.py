"""Repeatable synthetic policy benchmark, not a natural-language accuracy claim."""
import json
from pathlib import Path
from time import perf_counter
from uuid import uuid4

from graph import Store
from seed import seed


def main():
    store = Store('caseroute_eval_' + uuid4().hex)
    rows = []
    try:
        seed(store)
        # Six distinct policy conditions, four differently worded reports each.
        # The human-selected feature is available to both approaches.
        reports = ['Checkout fails when a discount is applied.', 'The cart rejects an active promotion.',
                   'A customer cannot complete the discounted purchase.', 'Payment stops after entering a coupon.']
        conditions = [
            ('normal', 'discounts', None, False, False, 'ready', 'pricing-cache', 'Commerce Engineering'),
            ('failed_check', 'discounts', None, True, False, 'ready', 'pricing-rule', 'Commerce Engineering'),
            ('changed_owner', 'discounts', None, False, True, 'ready', 'pricing-cache', 'Platform Reliability'),
            ('ambiguous', 'campaign', None, False, False, 'needs_service', None, None),
            ('selected_growth', 'campaign', 'campaigns', False, False, 'ready', 'campaign-window', 'Growth Platform'),
            ('selected_checkout', 'campaign', 'checkout', False, False, 'ready', 'checkout-trace', 'Commerce Engineering'),
        ]
        for condition, feature, selected, attempted, changed, status, aid, team in conditions:
            for report in reports:
                store.change_owner('pricing', 'platform' if changed else 'commerce')
                cid = store.create_case(feature, report)
                if attempted:
                    store.attempt(cid, 'pricing-cache', 'failed', 'Fixture: versions match')
                started = perf_counter()
                result = store.investigate(cid, selected)
                elapsed = round((perf_counter() - started) * 1000, 2)
                actual_action = result['action']['id'] if result['action'] else None
                actual_team = result['path'][-1] if result['status'] == 'ready' else None
                graph_ok = (result['status'], actual_action, actual_team) == (status, aid, team)
                # Baseline: feature/service text lookup against the same seeded runbooks
                # and ownership source, without relationship updates or attempt memory.
                baseline_action = 'campaign-window' if selected == 'campaigns' else 'checkout-trace' if feature == 'campaign' else 'pricing-cache'
                baseline_team = 'Growth Platform' if selected == 'campaigns' else 'Commerce Engineering'
                baseline_ok = ('ready', baseline_action, baseline_team) == (status, aid, team)
                rows.append(dict(condition=condition, report=report, graph_pass=graph_ok,
                                 baseline_pass=baseline_ok, latency_ms=elapsed,
                                 expected=[status, aid, team], actual=[result['status'], actual_action, actual_team]))
        latency = sorted(r['latency_ms'] for r in rows)
        result = dict(kind='Synthetic structured-context policy benchmark', scenarios=len(rows),
                      graph_pass=sum(r['graph_pass'] for r in rows),
                      static_lookup_pass=sum(r['baseline_pass'] for r in rows),
                      median_latency_ms=latency[len(latency)//2], max_latency_ms=max(latency),
                      limitations=['Authored alongside implementation; not independently held out.',
                                   'Reports are stored, not interpreted. Feature and optional service are human inputs.',
                                   'Static baseline lacks graph updates and attempt memory; this isolates their value, not graph superiority over every database.',
                                   'Single synthetic company, local database, no LLM, no load test.'], results=rows)
        Path('evaluation').mkdir(exist_ok=True)
        Path('evaluation/results.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
        print(json.dumps({k: v for k, v in result.items() if k != 'results'}, indent=2))
        if not all(r['graph_pass'] for r in rows):
            raise SystemExit(1)
    finally:
        store.graph.delete()


if __name__ == '__main__':
    main()
