"""Graph model of the open vehicle architecture.

Nodes are component instances (native components, custom nodes, signal blocks), edges are
typed signals "node.port" -> "node.port". The JSON format follows docs/specs/contracts.md
(section 4); in addition every node stores the component version it was saved with
("version") so that a later load can warn about deviations.

    g = Graph("demo", base_dt=0.01)
    g.add_node("src", "node/step", params={"t_step": 1.0})
    g.add_node("pt1", "node/lowpass", params={"T": 0.5})
    g.connect("src.y", "pt1.u")
    report = g.validate()          # ValidationReport (German messages), iterable over issues
    order = g.execution_order()    # deterministic topological order

Execution semantics used for ordering and loop detection:
    * an edge u.out -> v.in makes v depend on u, unless
        - the input port of v is a feedback port (Port.feedback=True: reads the previous step), or
        - u has no direct feedthrough (DIRECT_FEEDTHROUGH=False: its output only depends on its state);
    * a cycle of remaining edges is an algebraic loop (error).
"""

from __future__ import annotations

import copy
import heapq
import json
import math
import re
from dataclasses import dataclass, field, is_dataclass, asdict
from pathlib import Path

import numpy as np

from ..framework import plugins
from ..framework.component import set_param
from ..framework.types import TYPES, compatible

FORMAT_VERSION = 1
LOADER_PREFIXES = ("python", "rust", "cpp", "matlab")
PROJECT_ROOT = Path(__file__).resolve().parents[2]
_ID_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_\-]*$")


class GraphError(Exception):
    """Invalid graph operation (German message)."""


class GraphValidationError(GraphError):
    def __init__(self, report):
        super().__init__(report.text())
        self.report = report


# ---------------------------------------------------------------------------- validation report
@dataclass
class ValidationIssue:
    severity: str                 # "error" | "warning"
    code: str                     # machine readable, e.g. "type_mismatch", "algebraic_loop"
    message: str                  # German, for the editor
    node: str | None = None
    port: str | None = None
    connection: tuple | None = None   # (src, dst)
    nodes: list = field(default_factory=list)   # all nodes involved (loops)

    def __str__(self):
        return f"{'Fehler' if self.severity == 'error' else 'Warnung'}: {self.message}"

    def to_dict(self):
        return asdict(self)


class ValidationReport:
    def __init__(self, issues=None):
        self.issues = list(issues or [])

    def add(self, severity, code, message, **kw):
        self.issues.append(ValidationIssue(severity, code, message, **kw))

    def error(self, code, message, **kw):
        self.add("error", code, message, **kw)

    def warning(self, code, message, **kw):
        self.add("warning", code, message, **kw)

    @property
    def errors(self):
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self):
        return [i for i in self.issues if i.severity == "warning"]

    @property
    def ok(self):
        return not self.errors

    def codes(self):
        return [i.code for i in self.issues]

    def for_node(self, node_id):
        return [i for i in self.issues if i.node == node_id or node_id in i.nodes]

    def raise_for_errors(self):
        if self.errors:
            raise GraphValidationError(self)
        return self

    def text(self):
        if not self.issues:
            return "Graph ist gültig."
        return "\n".join(str(i) for i in self.issues)

    def to_dict(self):
        return {"ok": self.ok, "issues": [i.to_dict() for i in self.issues]}

    def __iter__(self):
        return iter(self.issues)

    def __len__(self):
        return len(self.issues)

    def __str__(self):
        return self.text()


# ---------------------------------------------------------------------------- nodes / connections
@dataclass
class Node:
    id: str
    component: str                       # spec string, e.g. "node/gain", "python:my.py:Cls"
    params: dict = field(default_factory=dict)
    period: float | None = None          # None = component PERIOD or every base step
    position: list = field(default_factory=lambda: [0.0, 0.0])
    label: str = ""
    version: str | None = None           # pinned component version (from file / last save)
    instance: object = field(default=None, repr=False, compare=False)
    error: str | None = None             # instantiation error (German)
    version_warning: str | None = None

    @property
    def effective_period(self):
        if self.period is not None:
            return self.period
        return getattr(self.instance, "PERIOD", None)

    @property
    def direct_feedthrough(self):
        return bool(getattr(self.instance, "DIRECT_FEEDTHROUGH", True))

    def to_dict(self):
        version = getattr(self.instance, "VERSION", None) or self.version
        out = {"id": self.id, "component": self.component, "params": _jsonable(self.params),
               "period": self.period, "position": [float(p) for p in self.position]}
        if self.label:
            out["label"] = self.label
        if version:
            out["version"] = version
        return out


@dataclass(frozen=True)
class Connection:
    src: str      # "node.port" (output)
    dst: str      # "node.port" (input)

    @property
    def src_node(self):
        return self.src.partition(".")[0]

    @property
    def src_port(self):
        return self.src.partition(".")[2]

    @property
    def dst_node(self):
        return self.dst.partition(".")[0]

    @property
    def dst_port(self):
        return self.dst.partition(".")[2]

    def to_dict(self):
        return {"from": self.src, "to": self.dst}

    def __str__(self):
        return f"{self.src} → {self.dst}"


def _jsonable(obj):
    if isinstance(obj, dict):
        return {str(k): _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    if is_dataclass(obj) and not isinstance(obj, type):
        return _jsonable(asdict(obj))
    return obj


def split_endpoint(text):
    node, sep, port = str(text).partition(".")
    if not sep or not node or not port:
        raise GraphError(f"Anschluss '{text}' muss die Form 'knoten.port' haben")
    return node, port


def resolve_spec(spec, base_dir=None):
    """Make relative paths of custom-node specs absolute (graph dir, cwd, project root)."""
    prefix, sep, rest = spec.partition(":")
    if not sep or prefix not in LOADER_PREFIXES or "/" in prefix:
        return spec
    path, cls = rest, ""
    if prefix == "python":
        m = re.match(r"^(.*?\.py)(?::([A-Za-z_]\w*))?$", rest)
        if m:
            path, cls = m.group(1), m.group(2) or ""
    p = Path(path)
    if not p.is_absolute():
        for root in [base_dir, Path.cwd(), PROJECT_ROOT]:
            if root is not None and (Path(root) / p).exists():
                p = (Path(root) / p).resolve()
                break
    out = f"{prefix}:{p.as_posix()}"
    return f"{out}:{cls}" if cls else out


def _port_signature(ports):
    ins, outs = ports
    return (tuple((k, v.type, v.optional, v.feedback) for k, v in ins.items()),
            tuple((k, v.type) for k, v in outs.items()))


# ---------------------------------------------------------------------------- graph
class Graph:
    def __init__(self, name="graph", base_dt=0.01, metadata=None, base_dir=None):
        self.name = name
        self.base_dt = float(base_dt)
        self.metadata = dict(metadata or {})
        self.nodes = {}               # id -> Node (insertion order = deterministic tie-break)
        self.connections = []         # list[Connection]
        self.base_dir = Path(base_dir) if base_dir else None
        self.path = None
        self.revision = 0             # incremented on every structural change (executor recompiles)
        self.load_warnings = []
        self._listeners = []

    # ------------------------------------------------------------------ change notification
    def on_change(self, callback):
        # callback(event: str, info: dict); returns the callback (use remove_listener to detach)
        self._listeners.append(callback)
        return callback

    def remove_listener(self, callback):
        if callback in self._listeners:
            self._listeners.remove(callback)

    def _changed(self, event, structural=True, **info):
        if structural:
            self.revision += 1
        for cb in list(self._listeners):
            cb(event, info)

    # ------------------------------------------------------------------ nodes
    def node(self, node_id):
        try:
            return self.nodes[node_id]
        except KeyError:
            raise GraphError(f"Knoten '{node_id}' existiert nicht") from None

    def instance(self, node_id):
        return self.node(node_id).instance

    def _new_id(self, component):
        base = re.sub(r"[^A-Za-z0-9_]", "_", component.rpartition("/")[2].partition("@")[0].rpartition(":")[2]
                      or "node").strip("_") or "node"
        if not base[0].isalpha() and base[0] != "_":
            base = "n_" + base
        i = 1
        while f"{base}{i}" in self.nodes:
            i += 1
        return f"{base}{i}"

    def add_node(self, id=None, component=None, params=None, period=None, position=None, label="", version=None,
                 strict=True, _notify=True):
        # Add a node; strict=True raises GraphError if the component cannot be created
        if component is None:
            raise GraphError("Komponente fehlt")
        node_id = id or self._new_id(component)
        if not _ID_RE.match(node_id):
            raise GraphError(f"Ungültige Knoten-ID '{node_id}' (erlaubt: Buchstaben, Ziffern, '_' und '-', "
                             f"kein Punkt)")
        if node_id in self.nodes:
            raise GraphError(f"Knoten '{node_id}' existiert bereits")
        node = Node(node_id, component, dict(params or {}), None if period is None else float(period),
                    list(position or [0.0, 0.0]), label or "", version)
        self._instantiate(node, use_pinned=version is not None)
        if strict and node.instance is None:
            raise GraphError(node.error)
        self.nodes[node_id] = node
        if _notify:
            self._changed("add_node", node=node_id)
        return node

    def _instantiate(self, node, use_pinned=False):
        spec = resolve_spec(node.component, self.base_dir)
        node.version_warning = None
        pinned_spec = None
        if use_pinned and node.version and ":" not in spec.split("/")[0]:
            try:
                kind, name, constraint = plugins.split_spec(spec)
                available = plugins.versions_of(kind, name)
                if node.version in available:
                    if plugins.version_matches(node.version, constraint):
                        pinned_spec = f"{kind}/{name}@{node.version}"
                        newer = [v for v in available if plugins.version_matches(v, constraint)
                                 and plugins.parse_version(v) > plugins.parse_version(node.version)]
                        if newer:
                            node.version_warning = (f"Knoten '{node.id}': gepinnte Version {node.version} von "
                                                    f"'{kind}/{name}' wird verwendet, neuere Version "
                                                    f"{max(newer, key=plugins.parse_version)} verfügbar")
                elif available:
                    node.version_warning = None   # set below after instantiation
            except ValueError:
                pass
        try:
            inst = plugins.create_component(pinned_spec or spec, dict(node.params) if node.params else None)
        except Exception as exc:  # noqa: BLE001 - report every creation problem in the editor
            node.instance = None
            node.error = self._describe_create_error(node, spec, exc)
            return False
        inst.instance_name = node.id
        node.instance, node.error = inst, None
        if node.version and getattr(inst, "VERSION", None) and inst.VERSION != node.version \
                and node.version_warning is None:
            node.version_warning = (f"Knoten '{node.id}': im Graph gepinnte Version {node.version}, geladen wurde "
                                    f"Version {inst.VERSION} ({node.component})")
        return True

    @staticmethod
    def _describe_create_error(node, spec, exc):
        prefix = spec.partition(":")[0]
        if prefix in LOADER_PREFIXES and ":" in spec:
            return f"Knoten '{node.id}': Custom Node '{node.component}' konnte nicht geladen werden: {exc}"
        try:
            kind, name, constraint = plugins.split_spec(spec)
        except ValueError:
            return (f"Knoten '{node.id}': ungültige Komponentenangabe '{spec}' "
                    f"(erwartet 'ebene/name[@version]' oder 'python:datei.py:Klasse')")
        versions = plugins.versions_of(kind, name)
        if not versions:
            known = sorted(d["name"] for d in plugins.available_components(kind))
            hint = f" Verfügbar in '{kind}': {', '.join(known)}" if known else ""
            return f"Knoten '{node.id}': unbekannte Komponente '{kind}/{name}'.{hint}"
        if isinstance(exc, KeyError):
            return (f"Knoten '{node.id}': keine Version von '{kind}/{name}' passt zu '{constraint}' "
                    f"(verfügbar: {', '.join(versions)})")
        if isinstance(exc, AttributeError):
            return f"Knoten '{node.id}': ungültiger Parameter für '{kind}/{name}': {exc}"
        return f"Knoten '{node.id}': Komponente '{spec}' konnte nicht erzeugt werden: {type(exc).__name__}: {exc}"

    def remove_node(self, node_id):
        node = self.node(node_id)
        self.connections = [c for c in self.connections if node_id not in (c.src_node, c.dst_node)]
        del self.nodes[node_id]
        for group in self.metadata.get("groups", {}).values():
            if node_id in group.get("nodes", []):
                group["nodes"].remove(node_id)
        close = getattr(node.instance, "close", None)
        if callable(close):
            close()
        self._changed("remove_node", node=node_id)
        return node

    def rename_node(self, old, new):
        if new == old:
            return
        if new in self.nodes:
            raise GraphError(f"Knoten '{new}' existiert bereits")
        if not _ID_RE.match(new):
            raise GraphError(f"Ungültige Knoten-ID '{new}'")
        node = self.node(old)
        self.nodes = {(new if k == old else k): v for k, v in self.nodes.items()}
        node.id = new
        if node.instance is not None:
            node.instance.instance_name = new

        def ren(ep):
            n, _, p = ep.partition(".")
            return f"{new}.{p}" if n == old else ep
        self.connections = [Connection(ren(c.src), ren(c.dst)) for c in self.connections]
        for group in self.metadata.get("groups", {}).values():
            group["nodes"] = [new if n == old else n for n in group.get("nodes", [])]
        self._changed("rename_node", old=old, new=new)

    def replace_component(self, node_id, component, keep_params=True, params=None):
        # Exchange the component of a node (same layer -> same ports); connections are kept
        node = self.node(node_id)
        new = Node(node.id, component, dict(params if params is not None else (node.params if keep_params else {})),
                   node.period, node.position, node.label)
        if not self._instantiate(new) and keep_params and params is None:
            new.params = {}
            self._instantiate(new)
        if new.instance is None:
            raise GraphError(new.error)
        close = getattr(node.instance, "close", None)
        if callable(close):
            close()
        node.component, node.params, node.instance, node.error, node.version = \
            component, new.params, new.instance, None, None
        self._changed("replace_component", node=node_id, component=component)
        return node

    def reinstantiate(self, node_id):
        node = self.node(node_id)
        ok = self._instantiate(node)
        self._changed("reinstantiate", node=node_id)
        return ok

    def replace_instance(self, node_id, instance, structural=True):
        # used by the hot reloader (already reset and state transferred)
        node = self.node(node_id)
        instance.instance_name = node_id
        node.instance, node.error = instance, None
        self._changed("replace_instance", structural=structural, node=node_id)

    def set_param(self, node_id, name, value):
        node = self.node(node_id)
        inst = node.instance
        if inst is not None:
            before = _port_signature(inst.ports())
            try:
                set_param(inst.params, name, value)
            except (AttributeError, TypeError, ValueError) as exc:
                raise GraphError(f"Parameter '{name}' von Knoten '{node_id}' kann nicht gesetzt werden: {exc}") \
                    from None
            obj = inst.params
            for part in name.split("."):
                obj = getattr(obj, part)
            value = _jsonable(obj)
            hook = getattr(inst, "params_changed", None)
            if callable(hook):
                hook(name)
            structural = _port_signature(inst.ports()) != before
        else:
            structural = False
        node.params[name] = value
        self._changed("param", structural=structural, node=node_id, name=name, value=value)
        return value

    def set_params(self, node_id, params):
        for k, v in params.items():
            self.set_param(node_id, k, v)

    def get_param(self, node_id, name):
        obj = self.node(node_id).instance.params
        for part in name.split("."):
            obj = getattr(obj, part)
        return obj

    def set_period(self, node_id, period):
        self.node(node_id).period = None if period is None else float(period)
        self._changed("period", node=node_id, period=period)

    def move_node(self, node_id, position):
        self.node(node_id).position = [float(position[0]), float(position[1])]
        self._changed("move", structural=False, node=node_id)

    def set_label(self, node_id, label):
        self.node(node_id).label = label
        self._changed("label", structural=False, node=node_id)

    # ------------------------------------------------------------------ groups (visual subsystems)
    def add_group(self, group_id, node_ids, label=""):
        for n in node_ids:
            self.node(n)
        self.metadata.setdefault("groups", {})[group_id] = {"label": label or group_id, "nodes": list(node_ids)}
        self._changed("group", structural=False, group=group_id)

    def remove_group(self, group_id, remove_nodes=False):
        group = self.metadata.get("groups", {}).pop(group_id, None)
        if group and remove_nodes:
            for n in list(group["nodes"]):
                if n in self.nodes:
                    self.remove_node(n)
        self._changed("group", structural=False, group=group_id)

    def group_of(self, node_id):
        for gid, group in self.metadata.get("groups", {}).items():
            if node_id in group.get("nodes", []):
                return gid
        return None

    # ------------------------------------------------------------------ ports / connections
    def ports(self, node_id):
        # (inputs, outputs): dicts name -> Port (instance level, custom nodes may be dynamic)
        inst = self.node(node_id).instance
        if inst is None:
            return {}, {}
        return inst.ports()

    def node_info(self, node_id):
        # describe() of the component plus instance-level ports and graph data (for the editor)
        node = self.node(node_id)
        info = type(node.instance).describe() if node.instance is not None else {}
        ins, outs = self.ports(node_id)
        info.update({"id": node.id, "spec": node.component, "label_override": node.label, "period_override":
                     node.period, "effective_period": node.effective_period, "error": node.error,
                     "inputs": {k: p.to_dict() for k, p in ins.items()},
                     "outputs": {k: p.to_dict() for k, p in outs.items()}})
        if node.instance is not None:
            info["version"] = node.instance.VERSION
            info["direct_feedthrough"] = node.direct_feedthrough
        return info

    def check_connection(self, src, dst):
        # German error message or None
        try:
            s_node, s_port = split_endpoint(src)
            d_node, d_port = split_endpoint(dst)
        except GraphError as exc:
            return str(exc)
        for n in (s_node, d_node):
            if n not in self.nodes:
                return f"Verbindung {src} → {dst}: Knoten '{n}' existiert nicht"
        if self.nodes[s_node].instance is None or self.nodes[d_node].instance is None:
            return None   # reported as component error
        _, outs = self.ports(s_node)
        ins, _ = self.ports(d_node)
        if s_port not in outs:
            src_ins, _ = self.ports(s_node)
            hint = " (das ist ein Eingang)" if s_port in src_ins else ""
            return (f"Verbindung {src} → {dst}: Knoten '{s_node}' hat keinen Ausgang '{s_port}'{hint}; "
                    f"vorhanden: {', '.join(outs) or 'keine'}")
        if d_port not in ins:
            _, dst_outs = self.ports(d_node)
            hint = " (das ist ein Ausgang)" if d_port in dst_outs else ""
            return (f"Verbindung {src} → {dst}: Knoten '{d_node}' hat keinen Eingang '{d_port}'{hint}; "
                    f"vorhanden: {', '.join(ins) or 'keine'}")
        t_out, t_in = outs[s_port].type, ins[d_port].type
        for t in (t_out, t_in):
            if t not in TYPES:
                return f"Verbindung {src} → {dst}: unbekannter Datentyp '{t}'"
        if not compatible(t_out, t_in):
            return (f"Typkonflikt: {src} liefert '{t_out}', {dst} erwartet '{t_in}'")
        return None

    def connect(self, src, dst, replace=False, check=True):
        if check:
            msg = self.check_connection(src, dst)
            if msg:
                raise GraphError(msg)
        else:
            split_endpoint(src)
            split_endpoint(dst)
        if any(c.src == src and c.dst == dst for c in self.connections):
            raise GraphError(f"Verbindung {src} → {dst} existiert bereits")
        existing = [c for c in self.connections if c.dst == dst]
        if existing:
            if not replace:
                raise GraphError(f"Eingang {dst} ist bereits mit {existing[0].src} verbunden "
                                 f"(zuerst trennen oder replace=True)")
            self.connections = [c for c in self.connections if c.dst != dst]
        conn = Connection(src, dst)
        self.connections.append(conn)
        self._changed("connect", src=src, dst=dst)
        return conn

    def disconnect(self, src=None, dst=None):
        # remove all connections matching src and/or dst; returns the number removed
        if src is None and dst is None:
            raise GraphError("disconnect() braucht src oder dst")
        keep, removed = [], 0
        for c in self.connections:
            if (src is None or c.src == src) and (dst is None or c.dst == dst):
                removed += 1
            else:
                keep.append(c)
        self.connections = keep
        if removed:
            self._changed("disconnect", src=src, dst=dst)
        return removed

    def connections_of(self, node_id):
        return [c for c in self.connections if node_id in (c.src_node, c.dst_node)]

    def source_of(self, dst):
        for c in self.connections:
            if c.dst == dst:
                return c.src
        return None

    # ------------------------------------------------------------------ timing
    def period_ticks(self, node_id):
        # number of base steps per sample of the node (>= 1), None if not an integer multiple
        period = self.node(node_id).effective_period
        if period is None or period <= 0:
            return 1
        ratio = period / self.base_dt
        ticks = int(round(ratio))
        if ticks < 1 or abs(ratio - ticks) > 1e-9 * max(1.0, ratio):
            return None
        return ticks

    # ------------------------------------------------------------------ ordering / loops
    def _dependency_edges(self):
        # adjacency among direct-feedthrough nodes: u -> [(v, connection)]
        adj = {nid: [] for nid, n in self.nodes.items() if n.instance is not None and n.direct_feedthrough}
        for c in self.connections:
            u, v = c.src_node, c.dst_node
            if u not in adj or v not in adj:
                continue
            ins, _ = self.ports(v)
            port = ins.get(c.dst_port)
            if port is None or port.feedback:
                continue
            _, outs = self.ports(u)
            if c.src_port not in outs:
                continue
            adj[u].append((v, c))
        return adj

    def algebraic_loops(self):
        # list of loops; each loop = list of connections forming one representative cycle
        adj = self._dependency_edges()
        index_of = {nid: i for i, nid in enumerate(self.nodes)}
        loops = []
        for scc in _tarjan(adj, index_of):
            members = set(scc)
            if len(scc) == 1 and not any(v == scc[0] for v, _ in adj[scc[0]]):
                continue
            loops.append(_cycle_in(scc[0], adj, members))
        return loops

    def execution_plan(self):
        # {"output": non-feedthrough nodes, "step": feedthrough nodes in topological order,
        #  "update": non-feedthrough nodes}; raises GraphValidationError on algebraic loops
        adj = self._dependency_edges()
        index_of = {nid: i for i, nid in enumerate(self.nodes)}
        indeg = {n: 0 for n in adj}
        for u, edges in adj.items():
            for v, _ in edges:
                indeg[v] += 1
        heap = [(index_of[n], n) for n, d in indeg.items() if d == 0]
        heapq.heapify(heap)
        order = []
        while heap:
            _, u = heapq.heappop(heap)
            order.append(u)
            for v, _ in adj[u]:
                indeg[v] -= 1
                if indeg[v] == 0:
                    heapq.heappush(heap, (index_of[v], v))
        if len(order) != len(adj):
            rep = ValidationReport()
            for loop in self.algebraic_loops():
                rep.error("algebraic_loop", _loop_message(loop), nodes=[c.dst_node for c in loop])
            raise GraphValidationError(rep)
        non_ft = [nid for nid, n in self.nodes.items() if n.instance is not None and not n.direct_feedthrough]
        return {"output": non_ft, "step": order, "update": list(non_ft)}

    def execution_order(self):
        plan = self.execution_plan()
        return plan["output"] + plan["step"]

    # ------------------------------------------------------------------ validation
    def validate(self):
        rep = ValidationReport()
        if not (self.base_dt > 0 and math.isfinite(self.base_dt)):
            rep.error("base_dt", f"Basisschritt base_dt={self.base_dt} muss positiv sein")
        for w in self.load_warnings:
            rep.warning("load", w)
        for nid, node in self.nodes.items():
            if node.instance is None:
                code = "component_load" if ":" in node.component.split("/")[0] else "component_unknown"
                rep.error(code, node.error or f"Knoten '{nid}': Komponente nicht geladen", node=nid)
                continue
            if node.version_warning:
                rep.warning("version_mismatch", node.version_warning, node=nid)
            ins, outs = self.ports(nid)
            for direction, ports in (("Eingang", ins), ("Ausgang", outs)):
                for pname, port in ports.items():
                    if port.type not in TYPES:
                        rep.error("unknown_type", f"{direction} {nid}.{pname}: unbekannter Datentyp '{port.type}'",
                                  node=nid, port=pname)
            period = node.effective_period
            if period is not None and (period <= 0 or not math.isfinite(period)):
                rep.error("period", f"Knoten '{nid}': Periode {period} s muss positiv sein", node=nid)
            elif self.base_dt > 0 and self.period_ticks(nid) is None:
                rep.error("period", f"Knoten '{nid}': Periode {period:g} s ist kein ganzzahliges Vielfaches des "
                                    f"Basisschritts {self.base_dt:g} s", node=nid)
        drivers = {}
        seen = set()
        for c in self.connections:
            if (c.src, c.dst) in seen:
                rep.warning("duplicate_connection", f"Verbindung {c} ist doppelt vorhanden", connection=(c.src, c.dst))
                continue
            seen.add((c.src, c.dst))
            msg = self.check_connection(c.src, c.dst)
            if msg:
                code = "type_mismatch" if msg.startswith("Typkonflikt") else "connection"
                rep.error(code, msg, node=c.dst_node if c.dst_node in self.nodes else None, port=c.dst_port,
                          connection=(c.src, c.dst))
            drivers.setdefault(c.dst, []).append(c.src)
        for dst, srcs in drivers.items():
            if len(srcs) > 1:
                rep.error("multiple_drivers", f"Eingang {dst} ist mehrfach belegt (von {', '.join(srcs)})",
                          node=dst.partition(".")[0], port=dst.partition(".")[2])
        for nid, node in self.nodes.items():
            if node.instance is None:
                continue
            ins, _ = self.ports(nid)
            for pname, port in ins.items():
                if not port.optional and f"{nid}.{pname}" not in drivers:
                    label = f" ({port.description})" if port.description else ""
                    rep.error("unconnected_input", f"Pflichteingang {nid}.{pname} ({port.type}){label} ist nicht "
                                                   f"verbunden", node=nid, port=pname)
        for loop in self.algebraic_loops():
            rep.error("algebraic_loop", _loop_message(loop), nodes=[c.dst_node for c in loop],
                      node=loop[0].dst_node)
        return rep

    # ------------------------------------------------------------------ serialization
    def to_dict(self):
        return {"format_version": FORMAT_VERSION, "name": self.name, "base_dt": self.base_dt,
                "nodes": [n.to_dict() for n in self.nodes.values()],
                "connections": [c.to_dict() for c in self.connections],
                "metadata": _jsonable(copy.deepcopy(self.metadata))}

    def to_json(self):
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data, base_dir=None, use_pinned=True):
        fv = int(data.get("format_version", 1))
        if fv > FORMAT_VERSION:
            raise GraphError(f"Graph-Format-Version {fv} wird nicht unterstützt (maximal {FORMAT_VERSION})")
        g = cls(data.get("name", "graph"), data.get("base_dt", 0.01), data.get("metadata"), base_dir)
        for nd in data.get("nodes", []):
            if "id" not in nd or "component" not in nd:
                g.load_warnings.append(f"Knoteneintrag ohne 'id' oder 'component' übersprungen: {nd}")
                continue
            node = Node(nd["id"], nd["component"], dict(nd.get("params") or {}), nd.get("period"),
                        list(nd.get("position") or [0.0, 0.0]), nd.get("label", ""), nd.get("version"))
            if node.id in g.nodes:
                g.load_warnings.append(f"Knoten-ID '{node.id}' ist doppelt; zweiter Eintrag übersprungen")
                continue
            g._instantiate(node, use_pinned=use_pinned)
            g.nodes[node.id] = node
        for cd in data.get("connections", []):
            try:
                split_endpoint(cd["from"])
                split_endpoint(cd["to"])
            except (GraphError, KeyError) as exc:
                g.load_warnings.append(f"Verbindung {cd} übersprungen: {exc}")
                continue
            g.connections.append(Connection(cd["from"], cd["to"]))
        g.revision = 0
        return g

    @classmethod
    def load(cls, path, use_pinned=True):
        path = Path(path)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise GraphError(f"Graphdatei {path} ist kein gültiges JSON: {exc}") from None
        g = cls.from_dict(data, base_dir=path.parent, use_pinned=use_pinned)
        g.path = path
        return g

    def save(self, path=None):
        path = Path(path or self.path)
        if path is None:
            raise GraphError("Kein Dateipfad angegeben")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_json() + "\n", encoding="utf-8")
        self.path = path
        if self.base_dir is None:
            self.base_dir = path.parent
        for node in self.nodes.values():
            if node.instance is not None:
                node.version = node.instance.VERSION
                node.version_warning = None
        return path

    def pin_versions(self):
        # rewrite registry specs to exact versions ("kind/name@1.2.0")
        for node in self.nodes.values():
            if node.instance is None or ":" in node.component.split("/")[0]:
                continue
            base = node.component.partition("@")[0]
            node.component = f"{base}@{node.instance.VERSION}"
            node.version = node.instance.VERSION
        self._changed("pin_versions", structural=False)

    def copy(self):
        g = Graph.from_dict(self.to_dict(), base_dir=self.base_dir)
        g.path = self.path
        return g

    def __repr__(self):
        return f"Graph({self.name!r}, {len(self.nodes)} Knoten, {len(self.connections)} Verbindungen)"


# ---------------------------------------------------------------------------- helpers
def _tarjan(adj, index_of):
    # iterative Tarjan SCC; deterministic order (node insertion order)
    index, low, on_stack, stack, result = {}, {}, set(), [], []
    counter = 0
    for root in sorted(adj, key=index_of.get):
        if root in index:
            continue
        work = [(root, 0)]
        while work:
            v, i = work.pop()
            if i == 0:
                index[v] = low[v] = counter
                counter += 1
                stack.append(v)
                on_stack.add(v)
            recurse = False
            edges = adj[v]
            while i < len(edges):
                w = edges[i][0]
                i += 1
                if w not in index:
                    work.append((v, i))
                    work.append((w, 0))
                    recurse = True
                    break
                if w in on_stack:
                    low[v] = min(low[v], index[w])
            if recurse:
                continue
            if low[v] == index[v]:
                comp = []
                while True:
                    w = stack.pop()
                    on_stack.discard(w)
                    comp.append(w)
                    if w == v:
                        break
                result.append(sorted(comp, key=index_of.get))
            if work:
                parent = work[-1][0]
                low[parent] = min(low[parent], low[v])
    return result


def _cycle_in(start, adj, members):
    # BFS from start back to start inside one SCC -> list of connections
    from collections import deque
    parent = {}
    queue = deque()
    for v, c in adj[start]:
        if v in members and v not in parent:
            parent[v] = (start, c)
            queue.append(v)
    while queue and start not in parent:
        u = queue.popleft()
        for v, c in adj[u]:
            if v in members and v not in parent:
                parent[v] = (u, c)
                queue.append(v)
    path, v = [], start
    while True:
        u, c = parent[v]
        path.append(c)
        v = u
        if v == start:
            break
    return list(reversed(path))


def _loop_message(loop):
    chain = ", ".join(str(c) for c in loop)
    nodes = " → ".join([loop[0].src_node] + [c.dst_node for c in loop])
    return (f"Algebraische Schleife {nodes} ({chain}). Abhilfe: einen Block ohne Durchgriff (z. B. "
            f"Verzögerung/UnitDelay oder Integrator) einfügen oder den Eingang als Rückführungs-Port "
            f"(feedback=True) deklarieren.")
