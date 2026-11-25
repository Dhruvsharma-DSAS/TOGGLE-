from datetime import datetime, timezone
from tools.review_decision import review

def evidence():
    return dict(source_url='https://app.flagsmith.com/project/1',last_computed=datetime.now(timezone.utc).isoformat(),
        control_exposures=1000,decision_exposures=1000,control_conversions=300,decision_conversions=380,
        chance_to_beat_control=.99,lift_interval_low=.05,lift_interval_high=.4,srm_warning=False,excluded_identities=0,
        guardrail_passed=True,synthetic=True)

def test_fail_closed_on_missing_data():
    assert review({}).startswith('KEEP RUNNING')

def test_split_failure_blocks_apparent_winner():
    data=evidence();data['srm_warning']=True
    assert review(data).startswith('HOLD')

def test_uncertainty_crossing_zero_blocks_rollout():
    data=evidence();data['lift_interval_low']=-.02
    assert review(data).startswith('KEEP RUNNING')

def test_synthetic_winner_is_never_claimed_as_business_effect():
    assert 'Synthetic evidence validates the pipeline only' in review(evidence())

def test_nan_and_string_booleans_fail_closed():
    data=evidence();data['chance_to_beat_control']=float('nan')
    assert review(data).startswith('KEEP RUNNING')
    data=evidence();data['srm_warning']='false'
    assert review(data).startswith('KEEP RUNNING')
