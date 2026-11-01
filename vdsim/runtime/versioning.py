"""Version store for graphs and component configurations.

    store = VersionStore("configs/graphs/my_stack.json")      # history in configs/graphs/.history/my_stack/
    v1 = store.snapshot(graph, "Regler getauscht")             # Version(id="v0001", hash, parent, ...)
    v2 = store.snapshot(graph, "Lookahead erhöht")
    print(store.diff("v0001", "v0002").text())                # structured + German text
    store.restore("v0001")                                     # writes the graph file, new snapshot

Every snapshot is the complete JSON document (content addressed by its SHA-256 hash), the
index (index.json) holds id, parent, timestamp, message, author, hash. Identical content as
the head version creates no new snapshot. Optionally each snapshot is committed with git
when the file lies inside a git repository (git="auto" | True | False).
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path


def canonical(doc):
    return json.dumps(doc, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str)


def content_hash(doc):
    return hashlib.sha256(canonical(doc).encode("utf-8")).hexdigest()


@dataclass
class Version:
    id: str
    hash: str
    parent: str | None
    timestamp: str
    message: str
    author: str = ""
    file: str = ""
    git_commit: str | None = None
    tags: list = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


# ---------------------------------------------------------------------------- diff
@dataclass
class GraphDiff:
    added_nodes: list = field(default_factory=list)          # node dicts
    removed_nodes: list = field(default_factory=list)
    changed_nodes: dict = field(default_factory=dict)        # id -> {field: (old, new)}; params flattened
    added_connections: list = field(default_factory=list)    # (src, dst)
    removed_connections: list = field(default_factory=list)
    changed_settings: dict = field(default_factory=dict)     # name/base_dt/metadata: (old, new)

    @property
    def empty(self):
        return not any([self.added_nodes, self.removed_nodes, self.changed_nodes, self.added_connections,
                        self.removed_connections, self.changed_settings])

    def to_dict(self):
        return asdict(self)

    def text(self):
        if self.empty:
            return "Keine Unterschiede."
        lines = []
        for k, (a, b) in self.changed_settings.items():
            lines.append(f"~ Einstellung {k}: {_fmt(a)} → {_fmt(b)}")
        for n in self.added_nodes:
            lines.append(f"+ Knoten {n['id']} ({n.get('component')})")
        for n in self.removed_nodes:
            lines.append(f"- Knoten {n['id']} ({n.get('component')})")
        for nid, changes in self.changed_nodes.items():
            for k, (a, b) in changes.items():
                lines.append(f"~ Knoten {nid}: {k}: {_fmt(a)} → {_fmt(b)}")
        for s, d in self.added_connections:
            lines.append(f"+ Verbindung {s} → {d}")
        for s, d in self.removed_connections:
            lines.append(f"- Verbindung {s} → {d}")
        return "\n".join(lines)

    def __str__(self):
        return self.text()


def _fmt(v):
    if v is _MISSING:
        return "(fehlt)"
    return json.dumps(v, ensure_ascii=False, default=str)


_MISSING = object()


def flatten_dict(d, prefix=""):
    out = {}
    for k, v in (d or {}).items():
        key = f"{prefix}{k}"
        if isinstance(v, dict) and v:
            out.update(flatten_dict(v, key + "."))
        else:
            out[key] = v
    return out


def diff_dicts(a, b):
    # flattened {key: (old, new)}; _MISSING for absent keys
    fa, fb = flatten_dict(a), flatten_dict(b)
    out = {}
    for k in list(fa) + [k for k in fb if k not in fa]:
        va, vb = fa.get(k, _MISSING), fb.get(k, _MISSING)
        if va != vb:
            out[k] = (va, vb)
    return out


def diff_graphs(a, b):
    """Structured diff of two graph documents (dicts in the contracts.md format)."""
    if hasattr(a, "to_dict"):
        a = a.to_dict()
    if hasattr(b, "to_dict"):
        b = b.to_dict()
    d = GraphDiff()
    for key in ("name", "base_dt", "format_version"):
        if a.get(key) != b.get(key):
            d.changed_settings[key] = (a.get(key, _MISSING), b.get(key, _MISSING))
    for k, v in diff_dicts(a.get("metadata", {}), b.get("metadata", {})).items():
        d.changed_settings[f"metadata.{k}"] = v
    na = {n["id"]: n for n in a.get("nodes", [])}
    nb = {n["id"]: n for n in b.get("nodes", [])}
    d.added_nodes = [nb[i] for i in nb if i not in na]
    d.removed_nodes = [na[i] for i in na if i not in nb]
    for i in na:
        if i not in nb:
            continue
        changes = {}
        for k in ("component", "version", "period", "label", "position"):
            if na[i].get(k) != nb[i].get(k):
                changes[k] = (na[i].get(k, _MISSING), nb[i].get(k, _MISSING))
        for k, v in diff_dicts(na[i].get("params", {}), nb[i].get("params", {})).items():
            changes[f"params.{k}"] = v
        if changes:
            d.changed_nodes[i] = changes
    ca = [(c["from"], c["to"]) for c in a.get("connections", [])]
    cb = [(c["from"], c["to"]) for c in b.get("connections", [])]
    d.added_connections = [c for c in cb if c not in ca]
    d.removed_connections = [c for c in ca if c not in cb]
    return d


@dataclass
class ConfigDiff:
    changes: dict

    @property
    def empty(self):
        return not self.changes

    def text(self):
        if not self.changes:
            return "Keine Unterschiede."
        return "\n".join(f"~ {k}: {_fmt(a)} → {_fmt(b)}" for k, (a, b) in self.changes.items())

    def __str__(self):
        return self.text()


def diff_documents(a, b):
    if isinstance(a, dict) and isinstance(b, dict) and "nodes" in a and "nodes" in b:
        return diff_graphs(a, b)
    return ConfigDiff(diff_dicts(a, b))


# ---------------------------------------------------------------------------- store
class VersionStore:
    def __init__(self, path, git="auto", author=""):
        self.path = Path(path).resolve()
        self.dir = self.path.parent / ".history" / self.path.stem
        self.git = git
        self.author = author

    # ------------------------------------------------------------------ index
    def _index_path(self):
        return self.dir / "index.json"

    def _read_index(self):
        p = self._index_path()
        if not p.exists():
            return {"file": self.path.name, "head": None, "versions": []}
        return json.loads(p.read_text(encoding="utf-8"))

    def _write_index(self, idx):
        self.dir.mkdir(parents=True, exist_ok=True)
        self._index_path().write_text(json.dumps(idx, indent=2, ensure_ascii=False), encoding="utf-8")

    def list(self):
        return [Version(**v) for v in self._read_index()["versions"]]

    @property
    def head(self):
        idx = self._read_index()
        return self.version(idx["head"]) if idx["head"] else None

    def version(self, vid):
        for v in self._read_index()["versions"]:
            if v["id"] == vid or v["hash"].startswith(str(vid)):
                return Version(**v)
        raise KeyError(f"Version '{vid}' nicht gefunden")

    def get(self, vid):
        v = self.version(vid)
        return json.loads((self.dir / v.file).read_text(encoding="utf-8"))

    # ------------------------------------------------------------------ operations
    def snapshot(self, doc=None, message="", author=None, force=False, write_file=True, tags=None):
        """Store a version of `doc` (Graph, dict, or None = current file content)."""
        if doc is None:
            doc = json.loads(self.path.read_text(encoding="utf-8"))
        elif hasattr(doc, "to_dict"):
            graph = doc
            doc = graph.to_dict()
            if write_file:
                graph.save(self.path)
                doc = graph.to_dict()
        elif write_file:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        h = content_hash(doc)
        idx = self._read_index()
        head = next((v for v in idx["versions"] if v["id"] == idx["head"]), None)
        if head is not None and head["hash"] == h and not force:
            return Version(**head)
        vid = f"v{len(idx['versions']) + 1:04d}"
        fname = f"{vid}_{h[:12]}.json"
        self.dir.mkdir(parents=True, exist_ok=True)
        (self.dir / fname).write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
        version = Version(vid, h, idx["head"], datetime.now(timezone.utc).isoformat(timespec="seconds"),
                          message, author if author is not None else self.author, fname, None, list(tags or []))
        idx["versions"].append(version.to_dict())
        idx["head"] = vid
        self._write_index(idx)
        if self._git_enabled():
            # the commit id is returned only (storing it would leave the index modified)
            version.git_commit = self._git_commit(f"{self.path.name} {vid}: {message}".strip())
        return version

    def diff(self, a, b=None):
        """Diff between two versions (b=None: current file content)."""
        da = self.get(a)
        db = self.get(b) if b is not None else json.loads(self.path.read_text(encoding="utf-8"))
        return diff_documents(da, db)

    def restore(self, vid, message=None):
        """Write version `vid` back to the file and record it as a new snapshot (history is kept)."""
        doc = self.get(vid)
        self.path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        v = self.snapshot(doc, message or f"Wiederhergestellt aus {vid}", write_file=False, force=True)
        return doc, v

    def log(self):
        lines = []
        for v in reversed(self.list()):
            lines.append(f"{v.id}  {v.timestamp}  {v.hash[:10]}  {v.message}"
                         + (f"  (Eltern: {v.parent})" if v.parent else ""))
        return "\n".join(lines)

    # ------------------------------------------------------------------ git
    def git_root(self):
        try:
            out = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=self.path.parent, capture_output=True,
                                 text=True, timeout=10)
        except (OSError, subprocess.SubprocessError):
            return None
        return Path(out.stdout.strip()) if out.returncode == 0 and out.stdout.strip() else None

    def _git_enabled(self):
        if self.git is False:
            return False
        return self.git_root() is not None

    def _git_commit(self, message):
        root = self.git_root()
        if root is None:
            return None
        try:
            subprocess.run(["git", "add", "--", str(self.path), str(self.dir)], cwd=root, capture_output=True,
                           text=True, timeout=30, check=True)
            res = subprocess.run(["git", "commit", "-m", message, "--", str(self.path), str(self.dir)], cwd=root,
                                 capture_output=True, text=True, timeout=30)
            if res.returncode != 0:
                return None
            head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, timeout=10)
            return head.stdout.strip() or None
        except (OSError, subprocess.SubprocessError):
            return None
