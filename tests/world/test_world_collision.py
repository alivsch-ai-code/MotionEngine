"""Tests for collision detection (SAT algorithm, rect_corners, collisions)."""

import numpy as np
import pytest

from vdsim.world.collision import pairwise_collisions, rect_corners, sat_overlap


class TestRectCorners:
    def test_unit_rectangle_at_origin(self):
        corners = rect_corners(0.0, 0.0, 0.0, 2.0, 1.0)
        assert corners.shape == (1, 4, 2)
        assert corners[0, :, 0].max() == pytest.approx(1.0)
        assert corners[0, :, 0].min() == pytest.approx(-1.0)
        assert corners[0, :, 1].max() == pytest.approx(0.5)
        assert corners[0, :, 1].min() == pytest.approx(-0.5)

    def test_rotated_90_degrees(self):
        corners = rect_corners(0.0, 0.0, np.pi / 2, 4.0, 2.0)
        assert corners[0, :, 0].max() == pytest.approx(1.0, abs=1e-10)
        assert corners[0, :, 1].max() == pytest.approx(2.0, abs=1e-10)

    def test_vectorized_multiple_rects(self):
        x = np.array([0.0, 10.0, 20.0])
        y = np.array([0.0, 0.0, 0.0])
        psi = np.array([0.0, 0.0, 0.0])
        corners = rect_corners(x, y, psi, 4.0, 2.0)
        assert corners.shape == (3, 4, 2)

    def test_offset_position(self):
        corners = rect_corners(5.0, 3.0, 0.0, 2.0, 2.0)
        center = corners[0].mean(axis=0)
        assert center[0] == pytest.approx(5.0, abs=1e-10)
        assert center[1] == pytest.approx(3.0, abs=1e-10)


class TestSATOverlap:
    def test_overlapping_rectangles(self):
        a = rect_corners(0.0, 0.0, 0.0, 4.0, 2.0)[0]
        b = rect_corners(1.0, 0.0, 0.0, 4.0, 2.0)
        result = sat_overlap(a, b)
        assert result[0]

    def test_separated_rectangles(self):
        a = rect_corners(0.0, 0.0, 0.0, 2.0, 2.0)[0]
        b = rect_corners(10.0, 0.0, 0.0, 2.0, 2.0)
        result = sat_overlap(a, b)
        assert not result[0]

    def test_touching_edge(self):
        a = rect_corners(0.0, 0.0, 0.0, 2.0, 2.0)[0]
        b = rect_corners(2.0, 0.0, 0.0, 2.0, 2.0)
        result = sat_overlap(a, b)
        assert isinstance(result[0], (bool, np.bool_))

    def test_rotated_overlap(self):
        a = rect_corners(0.0, 0.0, 0.0, 4.0, 2.0)[0]
        b = rect_corners(1.5, 0.0, np.pi / 4, 4.0, 2.0)
        result = sat_overlap(a, b)
        assert result[0]

    def test_multiple_targets(self):
        a = rect_corners(0.0, 0.0, 0.0, 4.0, 2.0)[0]
        b = rect_corners(
            np.array([1.0, 20.0, 0.5]),
            np.array([0.0, 0.0, 0.0]),
            np.array([0.0, 0.0, 0.0]),
            4.0,
            2.0,
        )
        result = sat_overlap(a, b)
        assert result.shape == (3,)
        assert result.tolist() == [True, False, True]

    def test_empty_targets(self):
        a = rect_corners(0.0, 0.0, 0.0, 4.0, 2.0)[0]
        b = np.zeros((0, 4, 2))
        result = sat_overlap(a, b)
        assert len(result) == 0


class TestPairwiseCollisions:
    def test_no_collisions(self):
        class Obj:
            def __init__(self, id, x, y, psi, length, width):
                self.id, self.x, self.y, self.psi = id, x, y, psi
                self.length, self.width = length, width

        objects = [
            Obj("a", 0, 0, 0, 2, 1),
            Obj("b", 100, 0, 0, 2, 1),
        ]
        pairs = pairwise_collisions(objects)
        assert len(pairs) == 0

    def test_two_colliding(self):
        class Obj:
            def __init__(self, id, x, y, psi, length, width):
                self.id, self.x, self.y, self.psi = id, x, y, psi
                self.length, self.width = length, width

        objects = [
            Obj("a", 0, 0, 0, 4, 2),
            Obj("b", 1, 0, 0, 4, 2),
        ]
        pairs = pairwise_collisions(objects)
        assert ("a", "b") in pairs

    def test_single_object(self):
        class Obj:
            def __init__(self, id, x, y, psi, length, width):
                self.id, self.x, self.y, self.psi = id, x, y, psi
                self.length, self.width = length, width

        assert pairwise_collisions([Obj("a", 0, 0, 0, 2, 1)]) == []

    def test_empty_list(self):
        assert pairwise_collisions([]) == []
