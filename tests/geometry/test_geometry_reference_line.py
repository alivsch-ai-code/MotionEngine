"""Tests for the ReferenceLine class (vdsim.geometry.reference_line).

Verifies Frenet transformations, projection, builders, and derived curves against
known analytical results.
"""

import numpy as np
import pytest

from vdsim.geometry.reference_line import ReferenceLine, wrap_angle


class TestWrapAngle:
    def test_within_range_unchanged(self):
        assert wrap_angle(0.0) == pytest.approx(0.0)
        assert wrap_angle(1.0) == pytest.approx(1.0)

    def test_wraps_positive(self):
        assert wrap_angle(2 * np.pi) == pytest.approx(0.0, abs=1e-10)

    def test_wraps_negative(self):
        assert wrap_angle(-2 * np.pi) == pytest.approx(0.0, abs=1e-10)

    def test_vectorized(self):
        result = wrap_angle(np.array([0, np.pi, 2 * np.pi, -np.pi]))
        assert result.shape == (4,)
        assert result[2] == pytest.approx(0.0, abs=1e-10)


class TestStraightLine:
    @pytest.fixture
    def line(self):
        return ReferenceLine.straight(100.0, ds=1.0)

    def test_length(self, line):
        assert line.length == pytest.approx(100.0)

    def test_zero_curvature(self, line):
        assert np.allclose(line.kappa, 0.0)

    def test_evaluate_midpoint(self, line):
        x, y, theta, kappa, dkappa = line.evaluate(50.0)
        assert x == pytest.approx(50.0, abs=1e-6)
        assert y == pytest.approx(0.0, abs=1e-6)
        assert theta == pytest.approx(0.0, abs=1e-6)

    def test_project_on_line(self, line):
        s, d = line.project(30.0, 5.0)
        assert s == pytest.approx(30.0, abs=0.1)
        assert d == pytest.approx(5.0, abs=0.1)

    def test_project_negative_d(self, line):
        s, d = line.project(50.0, -3.0)
        assert s == pytest.approx(50.0, abs=0.1)
        assert d == pytest.approx(-3.0, abs=0.1)


class TestCircularLine:
    @pytest.fixture
    def circle(self):
        return ReferenceLine.circle(50.0, ds=0.5)

    def test_closed(self, circle):
        assert circle.closed

    def test_constant_curvature(self, circle):
        assert np.allclose(circle.kappa, 1.0 / 50.0, atol=1e-10)

    def test_length_is_circumference(self, circle):
        assert circle.length == pytest.approx(2 * np.pi * 50.0, rel=1e-4)


class TestFrenetTransformations:
    @pytest.fixture
    def line(self):
        return ReferenceLine.straight(200.0, ds=0.5)

    def test_roundtrip_on_straight(self, line):
        x0, y0, theta0, v0, a0 = 50.0, 3.0, 0.05, 20.0, 0.5
        fs = line.to_frenet(x0, y0, theta0, 0.0, v0, a0)
        cart = line.to_cartesian(fs.s, fs.s_d, fs.s_dd, fs.d, fs.d_p, fs.d_pp)
        assert cart["x"] == pytest.approx(x0, abs=0.1)
        assert cart["y"] == pytest.approx(y0, abs=0.1)
        assert cart["v"] == pytest.approx(v0, abs=0.1)

    def test_on_curve_d_is_zero(self, line):
        fs = line.to_frenet(50.0, 0.0, 0.0, 0.0, 15.0, 0.0)
        assert fs.d == pytest.approx(0.0, abs=0.01)
        assert fs.d_p == pytest.approx(0.0, abs=0.01)


class TestProjectMany:
    def test_multiple_points(self):
        line = ReferenceLine.straight(100.0, ds=0.5)
        x = np.array([10.0, 30.0, 50.0, 70.0])
        y = np.array([2.0, -1.0, 0.0, 3.0])
        s, d = line.project_many(x, y)
        np.testing.assert_allclose(s, x, atol=0.5)
        np.testing.assert_allclose(d, y, atol=0.5)


class TestDerivedCurves:
    @pytest.fixture
    def line(self):
        return ReferenceLine.straight(100.0, ds=1.0)

    def test_offset_parallel(self, line):
        offset = line.offset(3.0)
        assert offset.length == pytest.approx(100.0, rel=0.01)
        _, y, _, _, _ = offset.evaluate(50.0)
        assert y == pytest.approx(3.0, abs=0.5)

    def test_resample_changes_point_count(self, line):
        resampled = line.resample(ds=2.0)
        assert len(resampled) < len(line)

    def test_segment_subrange(self, line):
        seg = line.segment(20.0, 60.0)
        assert seg.length == pytest.approx(40.0, rel=0.01)

    def test_reversed_opposite_direction(self, line):
        rev = line.reversed()
        assert rev.length == pytest.approx(line.length, rel=0.001)
        _, _, theta_rev, _, _ = rev.evaluate(0.0)
        assert abs(wrap_angle(theta_rev - np.pi)) < 0.1


class TestFromSegments:
    def test_straight_arc_straight(self):
        line = ReferenceLine.from_segments(
            [("straight", 50), ("arc", 50, 0.02), ("straight", 50)],
            ds=0.5,
        )
        assert line.length == pytest.approx(150.0, rel=0.05)

    def test_turn_segment(self):
        line = ReferenceLine.from_segments(
            [("straight", 30), ("turn", np.pi / 2, 50), ("straight", 30)],
            ds=0.5,
        )
        assert line.length > 60.0


class TestFromPoints:
    def test_smooth_through_noisy_points(self):
        t = np.linspace(0, 10, 50)
        x = t
        y = np.sin(t) + np.random.default_rng(0).normal(0, 0.01, len(t))
        line = ReferenceLine.from_points(x, y, smoothing=1.0)
        assert line.length > 8.0
        assert len(line) > 10


class TestSerialize:
    def test_to_dict_from_dict_roundtrip(self):
        original = ReferenceLine.straight(50.0, name="test")
        d = original.to_dict()
        restored = ReferenceLine.from_dict(d)
        assert restored.name == "test"
        assert restored.length == pytest.approx(original.length, rel=1e-6)
        np.testing.assert_allclose(restored.x, original.x, atol=1e-10)


class TestEdgeCases:
    def test_minimum_two_samples(self):
        with pytest.raises(ValueError, match="at least two samples"):
            ReferenceLine([0], [0], [0], [0], [0])

    def test_non_monotonic_s_raises(self):
        with pytest.raises(ValueError, match="strictly increasing"):
            ReferenceLine([0, 1, 0.5], [0, 1, 2], [0, 0, 0], [0, 0, 0], [0, 0, 0])
