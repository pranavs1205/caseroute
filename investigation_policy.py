"""Auditable evidence gates. Heuristics are not calibrated confidence scores."""
import re
from evidence_graph import stack_line

VERSION = 'graph-guidance-v3'
STEPS = ['check_environment', 'review_recorded_resolution', 'request_details']
MAINTENANCE = re.compile(r'^(?:rename|remove|replace|migrate|inline|assign|support|add support|use\s+\w+\(\))\b', re.I)


def guidance(context):
    if not context:
        return dict(policy=VERSION, report_kind='unknown', sufficient=False,
                    allowed_steps=['request_details'], recommended='request_details',
                    reasons=['No source evidence found.'], primary_components=[], missing=['Report details and reproduction'])
    issue = context['issue']
    title, description = issue['title'], issue.get('description') or ''
    title_words = set(re.findall(r'[a-z_]+', title.lower()))
    new_words = set(re.findall(r'[a-z_]+', description.lower())) - title_words
    sparse = len(description.strip()) < 80 or len(new_words) < 6
    maintenance = bool(MAINTENANCE.search(title))
    primary = [c for c in context.get('components', []) if c['field']=='title' or not (stack_line(c.get('excerpt','')) or re.search(
        r'(?:org\.apache\.spark\.(?:scheduler|shuffle)|\.java:\d|\.scala:\d)', c.get('excerpt','')))]
    dependency_failure = bool(re.search(r'NoClassDefFoundError|ClassNotFoundException|ModuleNotFoundError|ImportError', description))
    unclear_performance = bool(re.search(r'optimi[sz]|performance',title,re.I)) and len(description.strip()) < 200
    reasons, missing = [], []
    allowed = list(STEPS)
    if len(primary) >= 2:
        allowed.append('investigate_component_boundary')
    if sparse or unclear_performance:
        allowed = ['request_details']
        recommended = 'request_details'
        reasons.append('Source description is absent, short or adds too little beyond its title.')
        missing = ['Expected and actual behavior', 'Relevant source/change or minimal reproduction']
        if unclear_performance:
            reasons.append('Performance proposal lacks enough measurement context.')
            missing = ['Benchmark workload and baseline', 'Target metric and expected improvement']
    elif maintenance:
        recommended = 'review_recorded_resolution'
        reasons.append('Title indicates maintenance/enhancement; inspect the original change rather than treating it as an incident.')
    elif dependency_failure:
        recommended = 'check_environment'
        allowed = list(STEPS)
        reasons.append('An explicit missing-class/module error calls for dependency and classpath checks before broad component isolation.')
    elif len(primary) >= 3:
        recommended = 'investigate_component_boundary'
        reasons.append('At least three components have title/prose evidence beyond incidental stack frames.')
    else:
        recommended = 'check_environment'
        reasons.append('Confirm source-specific environment and reproduction before reusing this historical lead.')
    if context.get('memory') and context['memory'][0]['outcome'] in ('needs_more_info', 'not_applicable'):
        allowed, recommended = ['request_details'], 'request_details'
        reasons.append('The latest saved review requires new evidence before repeating this lead.')
    return dict(policy=VERSION, report_kind='maintenance_or_enhancement' if maintenance else 'incident_or_unknown',
                sufficient=not (sparse or unclear_performance), allowed_steps=allowed, recommended=recommended,
                reasons=reasons, primary_components=primary, missing=missing)
