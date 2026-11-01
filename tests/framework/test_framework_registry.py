"""Tests for the core plugin registry (vdsim.core.registry)."""

import pytest

from vdsim.core.registry import _REGISTRY, KINDS, available, create, get, register


class TestRegisterDecorator:
    def test_register_valid_kind(self):
        @register("vehicle_model", "test_model_reg")
        class Dummy:
            pass

        assert _REGISTRY["vehicle_model"]["test_model_reg"] is Dummy
        assert Dummy.registry_name == "test_model_reg"

    def test_register_invalid_kind_raises(self):
        with pytest.raises(ValueError, match="unknown registry kind"):

            @register("invalid_kind", "anything")
            class Bad:
                pass

    def test_register_overwrites_existing(self):
        @register("tire_model", "overwrite_test")
        class First:
            pass

        @register("tire_model", "overwrite_test")
        class Second:
            pass

        assert _REGISTRY["tire_model"]["overwrite_test"] is Second


class TestGet:
    def test_get_known_model(self):
        @register("vehicle_model", "get_test_model")
        class M:
            pass

        assert get("vehicle_model", "get_test_model") is M

    def test_get_unknown_raises_keyerror(self):
        with pytest.raises(KeyError, match="no vehicle_model named"):
            get("vehicle_model", "nonexistent_model_xyz")


class TestCreate:
    def test_create_instantiates(self):
        @register("vehicle_model", "create_test")
        class C:
            def __init__(self, value):
                self.value = value

        obj = create("vehicle_model", "create_test", 42)
        assert obj.value == 42


class TestAvailable:
    def test_available_returns_sorted_names(self):
        @register("tire_model", "a_tire_avail")
        class A:
            pass

        @register("tire_model", "b_tire_avail")
        class B:
            pass

        names = available("tire_model")
        assert "a_tire_avail" in names
        assert "b_tire_avail" in names
        assert names == sorted(names)


class TestKinds:
    def test_kinds_tuple_contains_expected(self):
        assert "vehicle_model" in KINDS
        assert "tire_model" in KINDS
        assert "lateral_controller" in KINDS
        assert "longitudinal_controller" in KINDS
        assert "maneuver" in KINDS
