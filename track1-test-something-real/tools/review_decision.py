"""Conservative review of manually transcribed Flagsmith evidence. No rollout mutations."""
import argparse
import json
import math
from datetime import datetime, timezone

def review(evidence):
    required=['source_url','last_computed','control_exposures','decision_exposures','control_conversions','decision_conversions',
              'chance_to_beat_control','lift_interval_low','lift_interval_high','srm_warning','excluded_identities','guardrail_passed','synthetic']
    if any(key not in evidence or evidence[key] is None for key in required):
        return 'KEEP RUNNING: evidence is incomplete.'
    if not isinstance(evidence['source_url'],str) or not evidence['source_url'].startswith('https://app.flagsmith.com/'):
        return 'KEEP RUNNING: attach the Flagsmith experiment source.'
    numeric=required[2:9]+['excluded_identities']
    if any(not isinstance(evidence[k],(int,float)) or isinstance(evidence[k],bool) or not math.isfinite(evidence[k]) for k in numeric):
        return 'KEEP RUNNING: evidence contains invalid numbers.'
    if any(type(evidence[k]) is not bool for k in ['srm_warning','guardrail_passed','synthetic']):
        return 'KEEP RUNNING: health checks must be explicit booleans.'
    for arm in ['control','decision']:
        n,c=evidence[arm+'_exposures'],evidence[arm+'_conversions']
        if n<50 or c<5: return 'KEEP RUNNING: minimum evidence floor not met.'
        if n!=int(n) or c!=int(c) or c>n: return 'KEEP RUNNING: inconsistent counts.'
    if not 0<=evidence['chance_to_beat_control']<=1 or evidence['lift_interval_low']>evidence['lift_interval_high']:
        return 'KEEP RUNNING: invalid probability or interval.'
    try:
        stamp=datetime.fromisoformat(evidence['last_computed'].replace('Z','+00:00'))
        age=(datetime.now(timezone.utc)-stamp).total_seconds()
        if age<0 or age>86400:return 'KEEP RUNNING: evidence is stale or future-dated.'
    except (ValueError,TypeError):return 'KEEP RUNNING: use a timezone-aware ISO timestamp.'
    if evidence['srm_warning'] or evidence['excluded_identities']!=0 or not evidence['guardrail_passed']:
        return 'HOLD: resolve split, identity, or guardrail health before rollout.'
    if evidence['chance_to_beat_control']>0.95 and evidence['lift_interval_low']>0:
        return 'REVIEW DECISION VARIANT: statistical gates pass. Human review required.'+(' Synthetic evidence validates the pipeline only.' if evidence['synthetic'] else '')
    return 'KEEP RUNNING: evidence does not pass the predeclared decision rule.'

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('evidence',help='JSON evidence transcribed from Flagsmith; see docs/results-template.json')
    args=parser.parse_args()
    try:
        with open(args.evidence) as f: evidence=json.load(f)
        print(review(evidence))
    except (OSError,ValueError,TypeError) as error:parser.exit(1,f'Cannot review evidence: {error}\n')
    print('This tool never ends experiments or changes flags. Review and perform any approved rollout in Flagsmith.')
