import pytest


@pytest.fixture(scope="session")
def kb():
    from vdsim.knowledge.collector import collect
    return collect()


@pytest.fixture(scope="session")
def graph(kb):
    from vdsim.knowledge.graph import build_graph
    return build_graph(kb)


@pytest.fixture(autouse=True)
def _math_cache(tmp_path_factory, monkeypatch):
    # formula images go to a temporary cache, not into the user profile
    monkeypatch.setenv("VDSIM_CACHE_DIR", str(tmp_path_factory.getbasetemp() / "cache"))
