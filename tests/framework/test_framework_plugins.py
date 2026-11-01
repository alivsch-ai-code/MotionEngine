"""Tests for the versioned plugin system (vdsim.framework.plugins)."""

import pytest

from vdsim.framework.plugins import (
    available_components,
    component,
    component_kinds,
    get_component,
    parse_version,
    split_spec,
    unregister,
    version_matches,
)


class TestParseVersion:
    def test_standard_semver(self):
        assert parse_version("1.2.3") == (1, 2, 3)

    def test_partial_version_padded(self):
        assert parse_version("2.1") == (2, 1, 0)
        assert parse_version("3") == (3, 0, 0)

    def test_empty_returns_zeros(self):
        assert parse_version("") == (0, 0, 0)


class TestVersionMatches:
    def test_wildcard(self):
        assert version_matches("1.0.0", "*")
        assert version_matches("1.0.0", "latest")
        assert version_matches("1.0.0", "")

    def test_exact_match(self):
        assert version_matches("1.2.3", "1.2.3")
        assert not version_matches("1.2.4", "1.2.3")

    def test_caret(self):
        assert version_matches("1.3.0", "^1.0.0")
        assert not version_matches("2.0.0", "^1.0.0")
        assert not version_matches("0.9.0", "^1.0.0")

    def test_tilde(self):
        assert version_matches("1.2.5", "~1.2.0")
        assert not version_matches("1.3.0", "~1.2.0")

    def test_gte(self):
        assert version_matches("2.0.0", ">=1.0.0")
        assert not version_matches("0.9.0", ">=1.0.0")


class TestSplitSpec:
    def test_simple_spec(self):
        kind, name, constraint = split_spec("vehicle_model/bicycle")
        assert kind == "vehicle_model"
        assert name == "bicycle"
        assert constraint == ""

    def test_spec_with_version(self):
        kind, name, constraint = split_spec("tire_model/pacejka@1.2.0")
        assert kind == "tire_model"
        assert name == "pacejka"
        assert constraint == "1.2.0"

    def test_invalid_spec_raises(self):
        with pytest.raises(ValueError, match="must look like"):
            split_spec("no_slash")


class TestComponentDecorator:
    def test_register_and_retrieve(self):
        @component(kind="test_kind", name="test_comp", version="1.0.0")
        class TestComp:
            KIND = "test_kind"
            NAME = "test_comp"
            VERSION = "1.0.0"

        cls = get_component("test_kind", "test_comp")
        assert cls is TestComp
        unregister("test_kind", "test_comp")

    def test_multiple_versions(self):
        @component(kind="test_kind", name="multi_v", version="1.0.0")
        class V1:
            KIND = "test_kind"
            NAME = "multi_v"
            VERSION = "1.0.0"

        @component(kind="test_kind", name="multi_v", version="2.0.0")
        class V2:
            KIND = "test_kind"
            NAME = "multi_v"
            VERSION = "2.0.0"

        assert get_component("test_kind/multi_v@^1") is V1
        assert get_component("test_kind/multi_v@^2") is V2
        assert get_component("test_kind/multi_v") is V2
        unregister("test_kind", "multi_v")


class TestGetComponent:
    def test_unknown_component_raises(self):
        with pytest.raises(KeyError, match="no component"):
            get_component("vehicle_model/totally_fake_model_xyz")


class TestAvailableComponents:
    def test_returns_list(self):
        result = available_components()
        assert isinstance(result, list)

    def test_filter_by_kind(self):
        all_comps = available_components()
        if all_comps:
            kind = all_comps[0]["kind"]
            filtered = available_components(kind)
            assert all(c["kind"] == kind for c in filtered)


class TestComponentKinds:
    def test_returns_sorted_list(self):
        kinds = component_kinds()
        assert kinds == sorted(kinds)
