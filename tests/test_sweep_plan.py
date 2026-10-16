"""Tests for scripts/sweep_plan.py feasibility + minimum-feature flag (Mac-side, needs shapely)."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
shapely = pytest.importorskip('shapely')
from sweep_plan import build_plan, DEFAULT_MIN_FEATURE_NM  # noqa: E402


def one(a, da, wa, **kw):
    return build_plan([a], [da], [wa], **kw)['combos'][0]


def test_default_threshold_is_30nm():
    assert DEFAULT_MIN_FEATURE_NM == 30.0


def test_thin_bridge_flagged_and_skipped_when_enforced():
    c = one(200, 0.48, 0.36)                    # ran in the a-sweep fill; ~9.5 nm bridges
    assert 8.5 < c['bridge_nm'] < 10.5
    assert c['status'] == 'below_min_feature' and c['run'] is False


def test_check_off_runs_but_still_flags():
    c = one(200, 0.48, 0.36, enforce_min_feature=False)
    assert c['status'] == 'below_min_feature' and c['run'] is True


def test_no_threshold_means_ok():
    c = one(200, 0.48, 0.36, min_feature_nm=None)
    assert c['status'] == 'ok' and c['run'] is True


def test_geometrically_infeasible_never_runs():
    for enforce in (True, False):
        c = one(275, 0.48, 0.43, enforce_min_feature=enforce)   # hole meets its images
        assert c['status'] == 'infeasible_geom' and c['run'] is False


def test_comfortable_cell_ok():
    c = one(400, 0.41, 0.22)
    assert c['status'] == 'ok' and c['run'] and c['bridge_nm'] > 80


def test_threshold_is_adjustable():
    assert one(400, 0.48, 0.22)['status'] == 'ok'                              # 35 nm bridge
    assert one(400, 0.48, 0.22, min_feature_nm=50)['status'] == 'below_min_feature'
