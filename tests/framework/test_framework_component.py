"""Tests for the Component base class (vdsim.framework.component)."""

from dataclasses import dataclass, field

import pytest

from vdsim.framework.component import (
    Component,
    NoParams,
    Port,
    params_from_dict,
    params_schema,
    params_to_dict,
    set_param,
)


class TestPort:
    def test_default_port(self):
        p = Port()
        assert p.type == "Any"
        assert not p.optional
        assert not p.feedback

    def test_port_to_dict(self):
        p = Port(type="EgoState", description="vehicle state", optional=True)
        d = p.to_dict()
        assert d["type"] == "EgoState"
        assert d["optional"] is True

    def test_feedback_port(self):
        p = Port(type="Status", feedback=True)
        assert p.feedback is True


class TestComponent:
    def test_default_class_attributes(self):
        assert Component.KIND == "node"
        assert Component.DIRECT_FEEDTHROUGH is True
        assert Component.API_VERSION == 1

    def test_spec_format(self):
        assert Component.spec() == "node/component@1.0.0"

    def test_describe_returns_dict(self):
        d = Component.describe()
        assert d["kind"] == "node"
        assert d["name"] == "component"
        assert "inputs" in d
        assert "outputs" in d
        assert "params" in d

    def test_input_output_ports(self):
        class MyComp(Component):
            INPUTS = {"ego": "EgoState"}
            OUTPUTS = {"cmd": Port(type="Command", unit="Nm")}

        inp = MyComp.input_ports()
        out = MyComp.output_ports()
        assert "ego" in inp
        assert inp["ego"].type == "EgoState"
        assert "cmd" in out
        assert out["cmd"].unit == "Nm"

    def test_step_not_implemented(self):
        c = Component()
        with pytest.raises(NotImplementedError):
            c.step(0.0, {})

    def test_get_set_state(self):
        c = Component()
        c.my_value = 42
        state = c.get_state()
        assert state["my_value"] == 42

        c2 = Component()
        c2.my_value = 0
        c2.set_state(state)
        assert c2.my_value == 42


class TestParamsHelpers:
    @dataclass
    class SampleParams:
        gain: float = 1.0
        offset: int = 0

    def test_params_from_dict(self):
        p = params_from_dict(self.SampleParams, {"gain": 2.5, "offset": 3})
        assert p.gain == 2.5
        assert p.offset == 3

    def test_params_to_dict(self):
        p = self.SampleParams(gain=3.0, offset=5)
        d = params_to_dict(p)
        assert d == {"gain": 3.0, "offset": 5}

    def test_set_param_simple(self):
        p = self.SampleParams()
        set_param(p, "gain", 10.0)
        assert p.gain == 10.0

    def test_set_param_unknown_raises(self):
        p = self.SampleParams()
        with pytest.raises(AttributeError, match="unknown parameter"):
            set_param(p, "nonexistent", 1)

    def test_set_param_nested(self):
        @dataclass
        class Inner:
            k: float = 0.5

        @dataclass
        class Outer:
            inner: Inner = field(default_factory=Inner)

        p = Outer()
        set_param(p, "inner.k", 2.0)
        assert p.inner.k == 2.0

    def test_params_schema(self):
        schema = params_schema(self.SampleParams)
        assert len(schema) == 2
        names = [s["name"] for s in schema]
        assert "gain" in names
        assert "offset" in names

    def test_no_params(self):
        schema = params_schema(NoParams)
        assert schema == []
