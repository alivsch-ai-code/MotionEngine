"""Code generator for the native node headers: vdsim_node.h (C++17) and vdsim_node.rs (Rust, std only).

Both are generated from vdsim.framework.types (field lists, defaults, object type codes,
codec version) plus the runtime codec extensions (vdsim.runtime.codecs), so native code
and the Python codecs cannot drift apart. They contain
    * the C ABI version and the layout constants (sizes, field offsets)
    * typed structs with decode/encode for EgoState, ControlCommand, ControllerStatus,
      ControlInput, ActuatorCommand, PlannedTrajectory (+ sample(t)), ObjectList/WorldState,
      Prediction, ReferenceLine and float/bool/Vector
    * Inputs/Outputs accessors, the Node base class / trait and the export macro
      (VDSIM_EXPORT_NODE / export_node!) that implements the complete C ABI.

    write_headers(dest_dir)            -> writes both files
    cpp_header(), rust_module()        -> text
"""

from __future__ import annotations

from pathlib import Path

from ..framework import types as T
from . import codecs as C

ABI_VERSION = 1

# ---------------------------------------------------------------------------- record descriptions
# field kinds: "f64", "i32", "bool", "opt" (NaN = not set / Option<f64>), ("arr", n)


def _records():
    ego = T.EgoState()
    cmd = T.ControlCommand()
    tp = T.TrajectoryPoint()
    obj = T.ObjectState()
    ci = T.ControlInput()
    ac = T.ActuatorCommand()
    st = T.ControllerStatus()
    recs = []
    recs.append(("EgoState", "EGO_STATE", "Fahrzeugzustand im Schwerpunkt (contracts.md, Abschn. 5)",
                 [(f, "i32" if f == "gear" else "f64", getattr(ego, f)) for f in T.EGO_FIELDS]))
    recs.append(("ControlCommand", "CONTROL_COMMAND", "Stellgrößen der Trajektorienregelung; NaN = nicht gesetzt",
                 [(f, "i32" if f == "direction" else ("f64" if f == "t" else "opt"), getattr(cmd, f))
                  for f in T.COMMAND_FIELDS]))
    recs.append(("ControllerStatus", "CONTROLLER_STATUS", "Trackingfehler und Reinitialisierungsanforderung",
                 [(f, "bool" if f == "reinit_request" else "f64", getattr(st, f)) for f in C.STATUS_FIELDS]))
    recs.append(("ControlInput", "CONTROL_INPUT", "an der Strecke wirksame Stellgrößen (je Rad: VL, VR, HL, HR)",
                 [(f, "f64" if n == 1 else ("arr", n), getattr(ci, f) if n == 1 else 0.0)
                  for f, n in C.CONTROL_INPUT_LAYOUT]))
    recs.append(("ActuatorCommand", "ACTUATOR_COMMAND", "radindividuelle Stellanforderungen",
                 [(f, "f64" if n == 1 else ("arr", n), getattr(ac, f) if n == 1 else 0.0)
                  for f, n in C.ACTUATOR_LAYOUT]))
    recs.append(("TrajectoryPoint", "TRAJECTORY_POINT", "Stützstelle der Solltrajektorie (absolute Zeit t)",
                 [(f, "f64", getattr(tp, f)) for f in T.TRAJECTORY_FIELDS]))
    recs.append(("ObjectState", "OBJECT", "Objekt (Mittelpunkt); type_code nach OBJECT_TYPES",
                 [("id", "i32", 0), ("type_code", "i32", 0)]
                 + [(f, "f64", getattr(obj, f)) for f in T.OBJECT_FIELDS[2:]]))
    recs.append(("PredictionPoint", "PREDICTION_POINT", "prädizierter Objektzustand",
                 [(f, "f64", 0.0) for f in T.PREDICTION_FIELDS]))
    recs.append(("ReferencePoint", "REFERENCE_POINT", "Stützstelle der Referenzkurve",
                 [(f, "f64", 0.0) for f in T.REFERENCE_FIELDS]))
    return recs


def _size(fields_):
    return sum(k[1] if isinstance(k, tuple) else 1 for _, k, _ in fields_)


def _cnum(v):
    v = float(v)
    if v != v:
        return "vdsim::nan()"
    text = repr(v)
    return text if ("." in text or "e" in text or "inf" in text) else text + ".0"


def _rnum(v):
    v = float(v)
    if v != v:
        return "f64::NAN"
    text = repr(v)
    return text if ("." in text or "e" in text) else text + ".0"


# ---------------------------------------------------------------------------- C++
def _cpp_layout(recs):
    lines = []
    for name, const, _, flds in recs:
        lines.append(f"// {name}")
        lines.append(f"constexpr size_t {const}_SIZE = {_size(flds)};")
        off = 0
        for f, kind, _ in flds:
            lines.append(f"constexpr size_t {const}_{f.upper()} = {off};")
            off += kind[1] if isinstance(kind, tuple) else 1
    lines.append("// PlannedTrajectory: header, then n x TrajectoryPoint")
    lines.append(f"constexpr size_t TRAJECTORY_HEADER_SIZE = {len(C.TRAJECTORY_HEADER)};")
    for i, f in enumerate(C.TRAJECTORY_HEADER):
        lines.append(f"constexpr size_t TRAJECTORY_HEADER_{f.upper()} = {i};")
    lines.append("// ObjectList / WorldState: [n], then n x ObjectState")
    lines.append("constexpr size_t OBJECT_LIST_HEADER_SIZE = 1;")
    lines.append("// Prediction: [n], then per object header + k x PredictionPoint")
    lines.append(f"constexpr size_t PREDICTED_OBJECT_HEADER_SIZE = {len(C.PREDICTED_OBJECT_HEADER)};")
    lines.append("// ReferenceLine: [n], then n x ReferencePoint")
    lines.append("constexpr size_t REFERENCE_LINE_HEADER_SIZE = 1;")
    return "\n".join(lines)


def _cpp_record(name, const, doc, flds):
    lines = [f"// {doc}", f"struct {name} {{"]
    for f, kind, default in flds:
        if kind == "f64":
            lines.append(f"  double {f} = {_cnum(default)};")
        elif kind == "opt":
            lines.append(f"  double {f} = vdsim::nan();  // NaN = nicht gesetzt")
        elif kind == "i32":
            lines.append(f"  int {f} = {int(default)};")
        elif kind == "bool":
            lines.append(f"  bool {f} = {'true' if default else 'false'};")
        else:
            lines.append(f"  double {f}[{kind[1]}] = {{}};")
    lines.append(f"  static constexpr size_t SIZE = layout::{const}_SIZE;")
    lines.append(f"  static {name} decode(const double* d, size_t n) {{")
    lines.append(f"    {name} v;")
    lines.append("    if (d == nullptr || n < SIZE) return v;")
    lines.append("    size_t i = 0;")
    for f, kind, _ in flds:
        if kind in ("f64", "opt"):
            lines.append(f"    v.{f} = d[i++];")
        elif kind == "i32":
            lines.append(f"    v.{f} = static_cast<int>(std::lround(d[i++]));")
        elif kind == "bool":
            lines.append(f"    v.{f} = d[i++] != 0.0;")
        else:
            lines.append(f"    for (size_t k = 0; k < {kind[1]}; ++k) v.{f}[k] = d[i++];")
    lines.append("    return v;")
    lines.append("  }")
    lines.append("  void encode(std::vector<double>& o) const {")
    for f, kind, _ in flds:
        if kind in ("f64", "opt"):
            lines.append(f"    o.push_back({f});")
        elif kind == "i32":
            lines.append(f"    o.push_back(static_cast<double>({f}));")
        elif kind == "bool":
            lines.append(f"    o.push_back({f} ? 1.0 : 0.0);")
        else:
            lines.append(f"    for (size_t k = 0; k < {kind[1]}; ++k) o.push_back({f}[k]);")
    lines.append("  }")
    lines.append("};")
    return "\n".join(lines)


_CPP_HEAD = r"""// vdsim_node.h - generated by vdsim.runtime.codegen from vdsim.framework.types. DO NOT EDIT.
// C ABI version @@ABI@@, codec version @@CODEC@@. Regenerate with:
//   python -c "from vdsim.runtime.codegen import write_headers; write_headers('.')"
//
// Usage (one translation unit):
//   #include "vdsim_node.h"
//   class MyNode : public vdsim::Node { ... };
//   VDSIM_EXPORT_NODE(MyNode, INFO_JSON)
#pragma once
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <exception>
#include <limits>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

#if defined(_WIN32)
#define VDSIM_EXPORT extern "C" __declspec(dllexport)
#else
#define VDSIM_EXPORT extern "C" __attribute__((visibility("default")))
#endif

namespace vdsim {

constexpr uint32_t ABI_VERSION = @@ABI@@;
constexpr uint32_t CODEC_VERSION = @@CODEC@@;
inline double nan() { return std::numeric_limits<double>::quiet_NaN(); }
inline bool is_set(double v) { return !std::isnan(v); }
inline double wrap_angle(double a) {
  const double pi = 3.14159265358979323846;
  return std::fmod(std::fmod(a + pi, 2.0 * pi) + 2.0 * pi, 2.0 * pi) - pi;
}

// object type codes (index in vdsim.framework.types.OBJECT_TYPES)
enum ObjectType : int { @@OBJECT_TYPES@@ };

namespace layout {
@@LAYOUT@@
}  // namespace layout

@@RECORDS@@

// Solltrajektorie (Arrays über die absolute Zeit)
struct PlannedTrajectory {
  int direction = 1;            // +1 vorwärts, -1 rückwärts
  int reference_point = 0;      // 0 = Schwerpunkt (cog), 1 = Hinterachse (rear_axle)
  double cost = 0.0;
  bool valid = true;
  std::vector<TrajectoryPoint> points;
  bool empty() const { return points.empty(); }
  size_t size() const { return points.size(); }
  static PlannedTrajectory decode(const double* d, size_t n) {
    PlannedTrajectory v;
    if (d == nullptr || n < layout::TRAJECTORY_HEADER_SIZE) return v;
    const size_t count = static_cast<size_t>(d[0]);
    v.direction = static_cast<int>(std::lround(d[1]));
    v.reference_point = static_cast<int>(std::lround(d[2]));
    v.cost = d[3];
    v.valid = d[4] != 0.0;
    size_t off = layout::TRAJECTORY_HEADER_SIZE;
    v.points.reserve(count);
    for (size_t k = 0; k < count && off + TrajectoryPoint::SIZE <= n; ++k, off += TrajectoryPoint::SIZE)
      v.points.push_back(TrajectoryPoint::decode(d + off, TrajectoryPoint::SIZE));
    return v;
  }
  void encode(std::vector<double>& o) const {
    o.push_back(static_cast<double>(points.size()));
    o.push_back(static_cast<double>(direction));
    o.push_back(static_cast<double>(reference_point));
    o.push_back(cost);
    o.push_back(valid ? 1.0 : 0.0);
    for (const auto& p : points) p.encode(o);
  }
  // interpolated point at absolute time t (clamped), like PlannedTrajectory.sample() in Python
  TrajectoryPoint sample(double t) const {
    TrajectoryPoint r;
    r.t = t;
    if (points.empty()) return r;
    if (points.size() == 1) { r = points[0]; r.t = t; return r; }
    size_t i = 0;
    double w = 0.0;
    if (t <= points.front().t) { i = 0; w = 0.0; }
    else if (t >= points.back().t) { i = points.size() - 2; w = 1.0; }
    else {
      size_t lo = 0, hi = points.size() - 1;
      while (hi - lo > 1) { size_t mid = (lo + hi) / 2; if (points[mid].t <= t) lo = mid; else hi = mid; }
      i = lo;
      const double dt = points[i + 1].t - points[i].t;
      w = (t - points[i].t) / (dt > 1e-12 ? dt : 1e-12);
    }
    const TrajectoryPoint& a = points[i];
    const TrajectoryPoint& b = points[i + 1];
@@LERP@@
    r.t = t;
    r.theta = a.theta + w * wrap_angle(b.theta - a.theta);
    return r;
  }
};

// Objektliste (auch Layout von WorldState)
struct ObjectList {
  std::vector<ObjectState> objects;
  static ObjectList decode(const double* d, size_t n) {
    ObjectList v;
    if (d == nullptr || n < 1) return v;
    const size_t count = static_cast<size_t>(d[0]);
    size_t off = 1;
    for (size_t k = 0; k < count && off + ObjectState::SIZE <= n; ++k, off += ObjectState::SIZE)
      v.objects.push_back(ObjectState::decode(d + off, ObjectState::SIZE));
    return v;
  }
  void encode(std::vector<double>& o) const {
    o.push_back(static_cast<double>(objects.size()));
    for (const auto& ob : objects) ob.encode(o);
  }
};
using WorldState = ObjectList;

struct PredictedObject {
  int id = 0;
  int type_code = 0;
  double length = 4.5;
  double width = 1.8;
  std::vector<PredictionPoint> points;
};

// prädizierte Objekttrajektorien
struct Prediction {
  std::vector<PredictedObject> objects;
  static Prediction decode(const double* d, size_t n) {
    Prediction v;
    if (d == nullptr || n < 1) return v;
    const size_t count = static_cast<size_t>(d[0]);
    size_t off = 1;
    for (size_t k = 0; k < count && off + layout::PREDICTED_OBJECT_HEADER_SIZE <= n; ++k) {
      PredictedObject ob;
      ob.id = static_cast<int>(std::lround(d[off]));
      ob.type_code = static_cast<int>(std::lround(d[off + 1]));
      ob.length = d[off + 2];
      ob.width = d[off + 3];
      const size_t m = static_cast<size_t>(d[off + 4]);
      off += layout::PREDICTED_OBJECT_HEADER_SIZE;
      for (size_t j = 0; j < m && off + PredictionPoint::SIZE <= n; ++j, off += PredictionPoint::SIZE)
        ob.points.push_back(PredictionPoint::decode(d + off, PredictionPoint::SIZE));
      v.objects.push_back(ob);
    }
    return v;
  }
  void encode(std::vector<double>& o) const {
    o.push_back(static_cast<double>(objects.size()));
    for (const auto& ob : objects) {
      o.push_back(static_cast<double>(ob.id));
      o.push_back(static_cast<double>(ob.type_code));
      o.push_back(ob.length);
      o.push_back(ob.width);
      o.push_back(static_cast<double>(ob.points.size()));
      for (const auto& p : ob.points) p.encode(o);
    }
  }
};

// Referenzkurve
struct ReferenceLine {
  std::vector<ReferencePoint> points;
  static ReferenceLine decode(const double* d, size_t n) {
    ReferenceLine v;
    if (d == nullptr || n < 1) return v;
    const size_t count = static_cast<size_t>(d[0]);
    size_t off = 1;
    for (size_t k = 0; k < count && off + ReferencePoint::SIZE <= n; ++k, off += ReferencePoint::SIZE)
      v.points.push_back(ReferencePoint::decode(d + off, ReferencePoint::SIZE));
    return v;
  }
  void encode(std::vector<double>& o) const {
    o.push_back(static_cast<double>(points.size()));
    for (const auto& p : points) p.encode(o);
  }
};

using Vector = std::vector<double>;

// ---------------------------------------------------------------------------- codecs
template <class T>
struct Codec {
  static T decode(const double* d, size_t n) { return T::decode(d, n); }
  static void encode(const T& v, std::vector<double>& o) { v.encode(o); }
};
template <>
struct Codec<double> {
  static double decode(const double* d, size_t n) { return (d != nullptr && n > 0) ? d[0] : 0.0; }
  static void encode(const double& v, std::vector<double>& o) { o.push_back(v); }
};
template <>
struct Codec<bool> {
  static bool decode(const double* d, size_t n) { return d != nullptr && n > 0 && d[0] != 0.0; }
  static void encode(const bool& v, std::vector<double>& o) { o.push_back(v ? 1.0 : 0.0); }
};
template <>
struct Codec<std::vector<double>> {
  static std::vector<double> decode(const double* d, size_t n) {
    return (d != nullptr && n > 0) ? std::vector<double>(d, d + n) : std::vector<double>();
  }
  static void encode(const std::vector<double>& v, std::vector<double>& o) { o.insert(o.end(), v.begin(), v.end()); }
};

// ---------------------------------------------------------------------------- node interface
class Inputs {
 public:
  Inputs(size_t n, const double* const* d, const size_t* len) : n_(n), d_(d), len_(len) {}
  size_t size() const { return n_; }
  bool has(size_t i) const { return i < n_ && d_ != nullptr && len_ != nullptr && len_[i] > 0 && d_[i] != nullptr; }
  const double* data(size_t i) const { return has(i) ? d_[i] : nullptr; }
  size_t len(size_t i) const { return has(i) ? len_[i] : 0; }
  // typed access; default-constructed value if the input is not connected / not yet available
  template <class T>
  T get(size_t i) const { return has(i) ? Codec<T>::decode(d_[i], len_[i]) : T(); }

 private:
  size_t n_;
  const double* const* d_;
  const size_t* len_;
};

class Outputs {
 public:
  void reset(size_t n) {
    if (bufs_.size() != n) { bufs_.assign(n, std::vector<double>()); set_.assign(n, 0); }
    for (size_t i = 0; i < n; ++i) { bufs_[i].clear(); set_[i] = 0; }
  }
  template <class T>
  void set(size_t i, const T& v) {
    if (i >= bufs_.size()) return;
    bufs_[i].clear();
    Codec<T>::encode(v, bufs_[i]);
    set_[i] = 1;
  }
  void set_raw(size_t i, const double* d, size_t n) {
    if (i >= bufs_.size()) return;
    bufs_[i].assign(d, d + n);
    set_[i] = 1;
  }
  // copy into host buffers; 1 = a buffer was too small (required sizes in len), 0 = ok
  int32_t deliver(size_t n, double* const* out, const size_t* cap, size_t* len) const {
    int32_t rc = 0;
    for (size_t i = 0; i < n; ++i) {
      if (i >= bufs_.size() || !set_[i]) { len[i] = 0; continue; }
      const std::vector<double>& b = bufs_[i];
      len[i] = b.size();
      if (b.size() > cap[i]) { rc = 1; continue; }
      if (!b.empty()) std::memcpy(out[i], b.data(), b.size() * sizeof(double));
    }
    return rc;
  }

 private:
  std::vector<std::vector<double>> bufs_;
  std::vector<char> set_;
};

inline double param(const double* p, size_t n, size_t i, double fallback) { return (p != nullptr && i < n) ? p[i] : fallback; }

class Node {
 public:
  virtual ~Node() = default;
  virtual void reset(double dt, uint64_t seed) { (void)dt; (void)seed; }
  // nodes with direct feedthrough
  virtual void step(double t, const Inputs& in, Outputs& out) {
    (void)t; (void)in; (void)out;
    throw std::runtime_error("step() ist nicht implementiert");
  }
  // nodes without direct feedthrough ("direct_feedthrough": false in node_info)
  virtual void output(double t, Outputs& out) { (void)t; (void)out; throw std::runtime_error("output() ist nicht implementiert"); }
  virtual void update(double t, const Inputs& in, double dt) {
    (void)t; (void)in; (void)dt;
    throw std::runtime_error("update() ist nicht implementiert");
  }
  // hot reload: complete internal state as flat double vector
  virtual std::vector<double> get_state() const { return std::vector<double>(); }
  virtual void set_state(const double* d, size_t n) { (void)d; (void)n; }
};

namespace detail {
struct Handle {
  std::unique_ptr<Node> node;
  Outputs out;
  std::string error;
  std::vector<double> state;
};
inline Handle* handle(void* h) { return static_cast<Handle*>(h); }
template <class F>
inline int32_t guarded(void* hp, F&& f) {
  Handle* h = handle(hp);
  if (h == nullptr) return -2;
  try {
    return f(h);
  } catch (const std::exception& e) {
    h->error = e.what();
  } catch (...) {
    h->error = "unbekannter C++-Fehler";
  }
  return -1;
}
}  // namespace detail
}  // namespace vdsim

// Implements the complete vdsim C ABI for NodeClass (constructor NodeClass(const double* params, size_t n)).
#define VDSIM_EXPORT_NODE(NodeClass, INFO_JSON)                                                              \
  VDSIM_EXPORT uint32_t vdsim_abi_version(void) { return vdsim::ABI_VERSION; }                               \
  VDSIM_EXPORT const char* vdsim_node_info(void) { return INFO_JSON; }                                       \
  VDSIM_EXPORT void* vdsim_create(const double* params, size_t n_params) {                                   \
    try {                                                                                                    \
      std::unique_ptr<vdsim::detail::Handle> h(new vdsim::detail::Handle());                                 \
      h->node.reset(new NodeClass(params, n_params));                                                        \
      return h.release();                                                                                    \
    } catch (...) {                                                                                          \
      return nullptr;                                                                                        \
    }                                                                                                        \
  }                                                                                                          \
  VDSIM_EXPORT void vdsim_destroy(void* h) { delete vdsim::detail::handle(h); }                              \
  VDSIM_EXPORT int32_t vdsim_reset(void* hp, double dt, uint64_t seed) {                                     \
    return vdsim::detail::guarded(hp, [&](vdsim::detail::Handle* h) { h->node->reset(dt, seed); return 0; }); \
  }                                                                                                          \
  VDSIM_EXPORT int32_t vdsim_step(void* hp, double t, size_t n_in, const double* const* in,                  \
                                  const size_t* in_len, size_t n_out, double* const* out,                    \
                                  const size_t* out_cap, size_t* out_len) {                                  \
    return vdsim::detail::guarded(hp, [&](vdsim::detail::Handle* h) {                                        \
      h->out.reset(n_out);                                                                                   \
      vdsim::Inputs inputs(n_in, in, in_len);                                                                \
      h->node->step(t, inputs, h->out);                                                                      \
      return h->out.deliver(n_out, out, out_cap, out_len);                                                   \
    });                                                                                                      \
  }                                                                                                          \
  VDSIM_EXPORT int32_t vdsim_fetch_outputs(void* hp, size_t n_out, double* const* out,                       \
                                           const size_t* out_cap, size_t* out_len) {                         \
    return vdsim::detail::guarded(hp, [&](vdsim::detail::Handle* h) {                                        \
      return h->out.deliver(n_out, out, out_cap, out_len);                                                   \
    });                                                                                                      \
  }                                                                                                          \
  VDSIM_EXPORT int32_t vdsim_output(void* hp, double t, size_t n_out, double* const* out,                    \
                                    const size_t* out_cap, size_t* out_len) {                                \
    return vdsim::detail::guarded(hp, [&](vdsim::detail::Handle* h) {                                        \
      h->out.reset(n_out);                                                                                   \
      h->node->output(t, h->out);                                                                            \
      return h->out.deliver(n_out, out, out_cap, out_len);                                                   \
    });                                                                                                      \
  }                                                                                                          \
  VDSIM_EXPORT int32_t vdsim_update(void* hp, double t, double dt, size_t n_in, const double* const* in,     \
                                    const size_t* in_len) {                                                  \
    return vdsim::detail::guarded(hp, [&](vdsim::detail::Handle* h) {                                        \
      vdsim::Inputs inputs(n_in, in, in_len);                                                                \
      h->node->update(t, inputs, dt);                                                                        \
      return 0;                                                                                              \
    });                                                                                                      \
  }                                                                                                          \
  VDSIM_EXPORT size_t vdsim_get_state(void* hp, double* buf, size_t cap) {                                   \
    vdsim::detail::Handle* h = vdsim::detail::handle(hp);                                                    \
    if (h == nullptr) return 0;                                                                              \
    try {                                                                                                    \
      h->state = h->node->get_state();                                                                       \
    } catch (...) {                                                                                          \
      h->state.clear();                                                                                      \
    }                                                                                                        \
    if (buf != nullptr && h->state.size() <= cap && !h->state.empty())                                       \
      std::memcpy(buf, h->state.data(), h->state.size() * sizeof(double));                                  \
    return h->state.size();                                                                                  \
  }                                                                                                          \
  VDSIM_EXPORT int32_t vdsim_set_state(void* hp, const double* buf, size_t n) {                              \
    return vdsim::detail::guarded(hp, [&](vdsim::detail::Handle* h) { h->node->set_state(buf, n); return 0; }); \
  }                                                                                                          \
  VDSIM_EXPORT const char* vdsim_last_error(void* hp) {                                                      \
    vdsim::detail::Handle* h = vdsim::detail::handle(hp);                                                    \
    return h == nullptr ? "" : h->error.c_str();                                                             \
  }
"""


def cpp_header():
    recs = _records()
    text = _CPP_HEAD
    text = text.replace("@@ABI@@", str(ABI_VERSION)).replace("@@CODEC@@", str(T.CODEC_VERSION))
    text = text.replace("@@OBJECT_TYPES@@", ", ".join(f"OBJECT_{n.upper()} = {i}" for i, n in enumerate(T.OBJECT_TYPES)))
    text = text.replace("@@LAYOUT@@", _cpp_layout(recs))
    text = text.replace("@@RECORDS@@", "\n\n".join(_cpp_record(*r) for r in recs))
    lerp = "\n".join(f"    r.{f} = a.{f} + w * (b.{f} - a.{f});" for f in T.TRAJECTORY_FIELDS if f not in ("t", "theta"))
    return text.replace("@@LERP@@", lerp)


# ---------------------------------------------------------------------------- Rust
def _rust_layout(recs):
    lines = []
    for name, const, _, flds in recs:
        lines.append(f"    // {name}")
        lines.append(f"    pub const {const}_SIZE: usize = {_size(flds)};")
        off = 0
        for f, kind, _ in flds:
            lines.append(f"    pub const {const}_{f.upper()}: usize = {off};")
            off += kind[1] if isinstance(kind, tuple) else 1
    lines.append(f"    pub const TRAJECTORY_HEADER_SIZE: usize = {len(C.TRAJECTORY_HEADER)};")
    for i, f in enumerate(C.TRAJECTORY_HEADER):
        lines.append(f"    pub const TRAJECTORY_HEADER_{f.upper()}: usize = {i};")
    lines.append("    pub const OBJECT_LIST_HEADER_SIZE: usize = 1;")
    lines.append(f"    pub const PREDICTED_OBJECT_HEADER_SIZE: usize = {len(C.PREDICTED_OBJECT_HEADER)};")
    lines.append("    pub const REFERENCE_LINE_HEADER_SIZE: usize = 1;")
    return "\n".join(lines)


def _rust_record(name, const, doc, flds):
    rtype = {"f64": "f64", "opt": "Option<f64>", "i32": "i32", "bool": "bool"}
    lines = [f"/// {doc}", "#[derive(Clone, Debug, PartialEq)]", f"pub struct {name} {{"]
    for f, kind, _ in flds:
        lines.append(f"    pub {f}: {rtype[kind] if not isinstance(kind, tuple) else f'[f64; {kind[1]}]'},")
    lines.append("}")
    lines.append(f"impl Default for {name} {{")
    lines.append("    fn default() -> Self {")
    lines.append("        Self {")
    for f, kind, default in flds:
        if kind == "f64":
            val = _rnum(default)
        elif kind == "opt":
            val = "None"
        elif kind == "i32":
            val = str(int(default))
        elif kind == "bool":
            val = "true" if default else "false"
        else:
            val = f"[0.0; {kind[1]}]"
        lines.append(f"            {f}: {val},")
    lines.append("        }")
    lines.append("    }")
    lines.append("}")
    lines.append(f"impl {name} {{")
    lines.append(f"    pub const SIZE: usize = layout::{const}_SIZE;")
    lines.append("}")
    lines.append(f"impl Codec for {name} {{")
    lines.append("    fn decode(d: &[f64]) -> Self {")
    lines.append("        let mut v = Self::default();")
    lines.append("        if d.len() < Self::SIZE {")
    lines.append("            return v;")
    lines.append("        }")
    lines.append("        let mut i = 0usize;")
    for f, kind, _ in flds:
        if kind == "f64":
            lines.append(f"        v.{f} = d[i];")
        elif kind == "opt":
            lines.append(f"        v.{f} = if d[i].is_nan() {{ None }} else {{ Some(d[i]) }};")
        elif kind == "i32":
            lines.append(f"        v.{f} = d[i].round() as i32;")
        elif kind == "bool":
            lines.append(f"        v.{f} = d[i] != 0.0;")
        else:
            lines.append(f"        v.{f}.copy_from_slice(&d[i..i + {kind[1]}]);")
        n = kind[1] if isinstance(kind, tuple) else 1
        lines.append(f"        i += {n};")
    lines.append("        let _ = i;")
    lines.append("        v")
    lines.append("    }")
    lines.append("    fn encode(&self, o: &mut Vec<f64>) {")
    for f, kind, _ in flds:
        if kind == "f64":
            lines.append(f"        o.push(self.{f});")
        elif kind == "opt":
            lines.append(f"        o.push(self.{f}.unwrap_or(f64::NAN));")
        elif kind == "i32":
            lines.append(f"        o.push(self.{f} as f64);")
        elif kind == "bool":
            lines.append(f"        o.push(if self.{f} {{ 1.0 }} else {{ 0.0 }});")
        else:
            lines.append(f"        o.extend_from_slice(&self.{f});")
    lines.append("    }")
    lines.append("}")
    return "\n".join(lines)


_RUST_HEAD = r"""//! vdsim_node.rs - generated by vdsim.runtime.codegen from vdsim.framework.types. DO NOT EDIT.
//! C ABI version @@ABI@@, codec version @@CODEC@@. Regenerate with:
//!   python -c "from vdsim.runtime.codegen import write_headers; write_headers('src')"
//!
//! Usage in lib.rs:
//!   #[macro_use]
//!   mod vdsim_node;
//!   use vdsim_node::*;
//!   struct MyNode { .. }
//!   impl Node for MyNode { .. }
//!   export_node!(MyNode, INFO_JSON);
#![allow(dead_code, unused_macros, clippy::all)]

use std::ffi::{c_char, c_void, CString};
use std::panic::{catch_unwind, AssertUnwindSafe};

pub const ABI_VERSION: u32 = @@ABI@@;
pub const CODEC_VERSION: u32 = @@CODEC@@;

/// object type codes (index in vdsim.framework.types.OBJECT_TYPES)
pub const OBJECT_TYPES: [&str; @@N_OBJECT_TYPES@@] = [@@OBJECT_TYPES@@];

pub mod layout {
@@LAYOUT@@
}

pub fn wrap_angle(a: f64) -> f64 {
    let pi = std::f64::consts::PI;
    ((a + pi) % (2.0 * pi) + 2.0 * pi) % (2.0 * pi) - pi
}

/// flat float64 codec (contracts.md, section 5)
pub trait Codec: Sized {
    fn decode(d: &[f64]) -> Self;
    fn encode(&self, o: &mut Vec<f64>);
}

impl Codec for f64 {
    fn decode(d: &[f64]) -> Self {
        d.first().copied().unwrap_or(0.0)
    }
    fn encode(&self, o: &mut Vec<f64>) {
        o.push(*self);
    }
}

impl Codec for bool {
    fn decode(d: &[f64]) -> Self {
        d.first().map_or(false, |v| *v != 0.0)
    }
    fn encode(&self, o: &mut Vec<f64>) {
        o.push(if *self { 1.0 } else { 0.0 });
    }
}

/// Vector
impl Codec for Vec<f64> {
    fn decode(d: &[f64]) -> Self {
        d.to_vec()
    }
    fn encode(&self, o: &mut Vec<f64>) {
        o.extend_from_slice(self);
    }
}

@@RECORDS@@

/// Solltrajektorie (Arrays über die absolute Zeit)
#[derive(Clone, Debug, PartialEq)]
pub struct PlannedTrajectory {
    pub direction: i32,       // +1 vorwärts, -1 rückwärts
    pub reference_point: i32, // 0 = Schwerpunkt (cog), 1 = Hinterachse (rear_axle)
    pub cost: f64,
    pub valid: bool,
    pub points: Vec<TrajectoryPoint>,
}
impl Default for PlannedTrajectory {
    fn default() -> Self {
        Self { direction: 1, reference_point: 0, cost: 0.0, valid: true, points: Vec::new() }
    }
}
impl Codec for PlannedTrajectory {
    fn decode(d: &[f64]) -> Self {
        let mut v = Self::default();
        if d.len() < layout::TRAJECTORY_HEADER_SIZE {
            return v;
        }
        let count = d[0] as usize;
        v.direction = d[1].round() as i32;
        v.reference_point = d[2].round() as i32;
        v.cost = d[3];
        v.valid = d[4] != 0.0;
        let mut off = layout::TRAJECTORY_HEADER_SIZE;
        for _ in 0..count {
            if off + TrajectoryPoint::SIZE > d.len() {
                break;
            }
            v.points.push(TrajectoryPoint::decode(&d[off..off + TrajectoryPoint::SIZE]));
            off += TrajectoryPoint::SIZE;
        }
        v
    }
    fn encode(&self, o: &mut Vec<f64>) {
        o.push(self.points.len() as f64);
        o.push(self.direction as f64);
        o.push(self.reference_point as f64);
        o.push(self.cost);
        o.push(if self.valid { 1.0 } else { 0.0 });
        for p in &self.points {
            p.encode(o);
        }
    }
}
impl PlannedTrajectory {
    pub fn is_empty(&self) -> bool {
        self.points.is_empty()
    }
    /// interpolated point at absolute time t (clamped), like PlannedTrajectory.sample() in Python
    pub fn sample(&self, t: f64) -> TrajectoryPoint {
        let n = self.points.len();
        if n == 0 {
            return TrajectoryPoint { t, ..Default::default() };
        }
        if n == 1 {
            return TrajectoryPoint { t, ..self.points[0].clone() };
        }
        let (i, w) = if t <= self.points[0].t {
            (0usize, 0.0)
        } else if t >= self.points[n - 1].t {
            (n - 2, 1.0)
        } else {
            let (mut lo, mut hi) = (0usize, n - 1);
            while hi - lo > 1 {
                let mid = (lo + hi) / 2;
                if self.points[mid].t <= t {
                    lo = mid;
                } else {
                    hi = mid;
                }
            }
            let dt = self.points[lo + 1].t - self.points[lo].t;
            (lo, (t - self.points[lo].t) / if dt > 1e-12 { dt } else { 1e-12 })
        };
        let a = &self.points[i];
        let b = &self.points[i + 1];
        TrajectoryPoint {
            t,
            theta: a.theta + w * wrap_angle(b.theta - a.theta),
@@LERP@@
        }
    }
}

/// Objektliste (auch Layout von WorldState)
#[derive(Clone, Debug, Default, PartialEq)]
pub struct ObjectList {
    pub objects: Vec<ObjectState>,
}
impl Codec for ObjectList {
    fn decode(d: &[f64]) -> Self {
        let mut v = Self::default();
        if d.is_empty() {
            return v;
        }
        let count = d[0] as usize;
        let mut off = 1;
        for _ in 0..count {
            if off + ObjectState::SIZE > d.len() {
                break;
            }
            v.objects.push(ObjectState::decode(&d[off..off + ObjectState::SIZE]));
            off += ObjectState::SIZE;
        }
        v
    }
    fn encode(&self, o: &mut Vec<f64>) {
        o.push(self.objects.len() as f64);
        for ob in &self.objects {
            ob.encode(o);
        }
    }
}
pub type WorldState = ObjectList;

#[derive(Clone, Debug, PartialEq)]
pub struct PredictedObject {
    pub id: i32,
    pub type_code: i32,
    pub length: f64,
    pub width: f64,
    pub points: Vec<PredictionPoint>,
}
impl Default for PredictedObject {
    fn default() -> Self {
        Self { id: 0, type_code: 0, length: 4.5, width: 1.8, points: Vec::new() }
    }
}

/// prädizierte Objekttrajektorien
#[derive(Clone, Debug, Default, PartialEq)]
pub struct Prediction {
    pub objects: Vec<PredictedObject>,
}
impl Codec for Prediction {
    fn decode(d: &[f64]) -> Self {
        let mut v = Self::default();
        if d.is_empty() {
            return v;
        }
        let count = d[0] as usize;
        let mut off = 1;
        for _ in 0..count {
            if off + layout::PREDICTED_OBJECT_HEADER_SIZE > d.len() {
                break;
            }
            let mut ob = PredictedObject {
                id: d[off].round() as i32,
                type_code: d[off + 1].round() as i32,
                length: d[off + 2],
                width: d[off + 3],
                points: Vec::new(),
            };
            let m = d[off + 4] as usize;
            off += layout::PREDICTED_OBJECT_HEADER_SIZE;
            for _ in 0..m {
                if off + PredictionPoint::SIZE > d.len() {
                    break;
                }
                ob.points.push(PredictionPoint::decode(&d[off..off + PredictionPoint::SIZE]));
                off += PredictionPoint::SIZE;
            }
            v.objects.push(ob);
        }
        v
    }
    fn encode(&self, o: &mut Vec<f64>) {
        o.push(self.objects.len() as f64);
        for ob in &self.objects {
            o.push(ob.id as f64);
            o.push(ob.type_code as f64);
            o.push(ob.length);
            o.push(ob.width);
            o.push(ob.points.len() as f64);
            for p in &ob.points {
                p.encode(o);
            }
        }
    }
}

/// Referenzkurve
#[derive(Clone, Debug, Default, PartialEq)]
pub struct ReferenceLine {
    pub points: Vec<ReferencePoint>,
}
impl Codec for ReferenceLine {
    fn decode(d: &[f64]) -> Self {
        let mut v = Self::default();
        if d.is_empty() {
            return v;
        }
        let count = d[0] as usize;
        let mut off = 1;
        for _ in 0..count {
            if off + ReferencePoint::SIZE > d.len() {
                break;
            }
            v.points.push(ReferencePoint::decode(&d[off..off + ReferencePoint::SIZE]));
            off += ReferencePoint::SIZE;
        }
        v
    }
    fn encode(&self, o: &mut Vec<f64>) {
        o.push(self.points.len() as f64);
        for p in &self.points {
            p.encode(o);
        }
    }
}

// ---------------------------------------------------------------------------- node interface
/// typed read access to the input buffers (index = position in node_info "inputs")
pub struct Inputs<'a> {
    bufs: Vec<&'a [f64]>,
}
impl<'a> Inputs<'a> {
    /// # Safety
    /// pointers must come from the vdsim host (n valid entries)
    pub unsafe fn from_raw(n: usize, ptrs: *const *const f64, lens: *const usize) -> Inputs<'a> {
        let mut bufs: Vec<&'a [f64]> = Vec::with_capacity(n);
        for i in 0..n {
            let p = if ptrs.is_null() { std::ptr::null() } else { *ptrs.add(i) };
            let l = if lens.is_null() { 0 } else { *lens.add(i) };
            bufs.push(if p.is_null() || l == 0 { &[] } else { std::slice::from_raw_parts(p, l) });
        }
        Inputs { bufs }
    }
    pub fn len(&self) -> usize {
        self.bufs.len()
    }
    pub fn has(&self, i: usize) -> bool {
        self.bufs.get(i).map_or(false, |b| !b.is_empty())
    }
    pub fn raw(&self, i: usize) -> &[f64] {
        self.bufs.get(i).copied().unwrap_or(&[])
    }
    /// None if the input is not connected / not yet available
    pub fn get<T: Codec>(&self, i: usize) -> Option<T> {
        if self.has(i) {
            Some(T::decode(self.bufs[i]))
        } else {
            None
        }
    }
    pub fn get_or_default<T: Codec + Default>(&self, i: usize) -> T {
        self.get(i).unwrap_or_default()
    }
}

/// output values of one call (index = position in node_info "outputs"); unset = keep previous value
#[derive(Default)]
pub struct Outputs {
    bufs: Vec<Vec<f64>>,
    set: Vec<bool>,
}
impl Outputs {
    pub fn reset(&mut self, n: usize) {
        if self.bufs.len() != n {
            self.bufs = vec![Vec::new(); n];
            self.set = vec![false; n];
        }
        for i in 0..n {
            self.bufs[i].clear();
            self.set[i] = false;
        }
    }
    pub fn set<T: Codec>(&mut self, i: usize, v: &T) {
        if i < self.bufs.len() {
            self.bufs[i].clear();
            v.encode(&mut self.bufs[i]);
            self.set[i] = true;
        }
    }
    pub fn set_raw(&mut self, i: usize, d: &[f64]) {
        if i < self.bufs.len() {
            self.bufs[i].clear();
            self.bufs[i].extend_from_slice(d);
            self.set[i] = true;
        }
    }
    /// # Safety
    /// host buffers with n entries; returns 1 if a buffer is too small (required sizes in lens)
    pub unsafe fn deliver(&self, n: usize, ptrs: *const *mut f64, caps: *const usize, lens: *mut usize) -> i32 {
        let mut rc = 0;
        for i in 0..n {
            let len_p = lens.add(i);
            if i >= self.bufs.len() || !self.set[i] {
                *len_p = 0;
                continue;
            }
            let b = &self.bufs[i];
            *len_p = b.len();
            if b.len() > *caps.add(i) {
                rc = 1;
                continue;
            }
            if !b.is_empty() {
                std::ptr::copy_nonoverlapping(b.as_ptr(), *ptrs.add(i), b.len());
            }
        }
        rc
    }
}

/// parameter i of the create() array (declared order in node_info "params")
pub fn param(params: &[f64], i: usize, default: f64) -> f64 {
    params.get(i).copied().unwrap_or(default)
}

/// the node interface (same lifecycle as vdsim.framework.Component)
pub trait Node {
    fn new(params: &[f64]) -> Self
    where
        Self: Sized;
    fn reset(&mut self, _dt: f64, _seed: u64) {}
    /// nodes with direct feedthrough
    fn step(&mut self, _t: f64, _inputs: &Inputs, _outputs: &mut Outputs) -> Result<(), String> {
        Err("step() ist nicht implementiert".to_string())
    }
    /// nodes without direct feedthrough ("direct_feedthrough": false)
    fn output(&mut self, _t: f64, _outputs: &mut Outputs) -> Result<(), String> {
        Err("output() ist nicht implementiert".to_string())
    }
    fn update(&mut self, _t: f64, _inputs: &Inputs, _dt: f64) -> Result<(), String> {
        Err("update() ist nicht implementiert".to_string())
    }
    /// hot reload: complete internal state as flat f64 vector
    fn get_state(&self) -> Vec<f64> {
        Vec::new()
    }
    fn set_state(&mut self, _state: &[f64]) {}
}

pub struct Handle<N: Node> {
    pub node: N,
    pub out: Outputs,
    pub error: CString,
    pub state: Vec<f64>,
}

fn panic_text(p: Box<dyn std::any::Any + Send>) -> String {
    if let Some(s) = p.downcast_ref::<&str>() {
        format!("Panik: {}", s)
    } else if let Some(s) = p.downcast_ref::<String>() {
        format!("Panik: {}", s)
    } else {
        "Panik im Rust-Node".to_string()
    }
}

impl<N: Node> Handle<N> {
    fn fail(&mut self, msg: String) -> i32 {
        self.error = CString::new(msg.replace('\0', " ")).unwrap_or_default();
        -1
    }
}

// generic implementations of the C ABI functions (called by export_node!)
pub mod ffi {
    use super::*;

    pub unsafe fn create<N: Node>(params: *const f64, n: usize) -> *mut c_void {
        let p: &[f64] = if params.is_null() || n == 0 { &[] } else { std::slice::from_raw_parts(params, n) };
        match catch_unwind(AssertUnwindSafe(|| N::new(p))) {
            Ok(node) => Box::into_raw(Box::new(Handle {
                node,
                out: Outputs::default(),
                error: CString::default(),
                state: Vec::new(),
            })) as *mut c_void,
            Err(_) => std::ptr::null_mut(),
        }
    }
    pub unsafe fn destroy<N: Node>(h: *mut c_void) {
        if !h.is_null() {
            drop(Box::from_raw(h as *mut Handle<N>));
        }
    }
    unsafe fn handle<'a, N: Node>(h: *mut c_void) -> Option<&'a mut Handle<N>> {
        (h as *mut Handle<N>).as_mut()
    }
    pub unsafe fn reset<N: Node>(h: *mut c_void, dt: f64, seed: u64) -> i32 {
        let Some(h) = handle::<N>(h) else { return -2 };
        match catch_unwind(AssertUnwindSafe(|| h.node.reset(dt, seed))) {
            Ok(()) => 0,
            Err(p) => h.fail(panic_text(p)),
        }
    }
    #[allow(clippy::too_many_arguments)]
    pub unsafe fn step<N: Node>(h: *mut c_void, t: f64, n_in: usize, inp: *const *const f64, in_len: *const usize,
                                n_out: usize, out: *const *mut f64, out_cap: *const usize, out_len: *mut usize) -> i32 {
        let Some(h) = handle::<N>(h) else { return -2 };
        let inputs = Inputs::from_raw(n_in, inp, in_len);
        h.out.reset(n_out);
        let node = &mut h.node;
        let outputs = &mut h.out;
        match catch_unwind(AssertUnwindSafe(|| node.step(t, &inputs, outputs))) {
            Ok(Ok(())) => h.out.deliver(n_out, out, out_cap, out_len),
            Ok(Err(e)) => h.fail(e),
            Err(p) => h.fail(panic_text(p)),
        }
    }
    pub unsafe fn fetch_outputs<N: Node>(h: *mut c_void, n_out: usize, out: *const *mut f64, out_cap: *const usize,
                                         out_len: *mut usize) -> i32 {
        let Some(h) = handle::<N>(h) else { return -2 };
        h.out.deliver(n_out, out, out_cap, out_len)
    }
    pub unsafe fn output<N: Node>(h: *mut c_void, t: f64, n_out: usize, out: *const *mut f64, out_cap: *const usize,
                                  out_len: *mut usize) -> i32 {
        let Some(h) = handle::<N>(h) else { return -2 };
        h.out.reset(n_out);
        let node = &mut h.node;
        let outputs = &mut h.out;
        match catch_unwind(AssertUnwindSafe(|| node.output(t, outputs))) {
            Ok(Ok(())) => h.out.deliver(n_out, out, out_cap, out_len),
            Ok(Err(e)) => h.fail(e),
            Err(p) => h.fail(panic_text(p)),
        }
    }
    pub unsafe fn update<N: Node>(h: *mut c_void, t: f64, dt: f64, n_in: usize, inp: *const *const f64,
                                  in_len: *const usize) -> i32 {
        let Some(h) = handle::<N>(h) else { return -2 };
        let inputs = Inputs::from_raw(n_in, inp, in_len);
        let node = &mut h.node;
        match catch_unwind(AssertUnwindSafe(|| node.update(t, &inputs, dt))) {
            Ok(Ok(())) => 0,
            Ok(Err(e)) => h.fail(e),
            Err(p) => h.fail(panic_text(p)),
        }
    }
    pub unsafe fn get_state<N: Node>(h: *mut c_void, buf: *mut f64, cap: usize) -> usize {
        let Some(h) = handle::<N>(h) else { return 0 };
        let node = &h.node;
        h.state = catch_unwind(AssertUnwindSafe(|| node.get_state())).unwrap_or_default();
        if !buf.is_null() && !h.state.is_empty() && h.state.len() <= cap {
            std::ptr::copy_nonoverlapping(h.state.as_ptr(), buf, h.state.len());
        }
        h.state.len()
    }
    pub unsafe fn set_state<N: Node>(h: *mut c_void, buf: *const f64, n: usize) -> i32 {
        let Some(h) = handle::<N>(h) else { return -2 };
        let s: &[f64] = if buf.is_null() || n == 0 { &[] } else { std::slice::from_raw_parts(buf, n) };
        let node = &mut h.node;
        match catch_unwind(AssertUnwindSafe(|| node.set_state(s))) {
            Ok(()) => 0,
            Err(p) => h.fail(panic_text(p)),
        }
    }
    pub unsafe fn last_error<N: Node>(h: *mut c_void) -> *const c_char {
        static EMPTY: &[u8] = b"\0";
        match handle::<N>(h) {
            Some(h) => h.error.as_ptr(),
            None => EMPTY.as_ptr() as *const c_char,
        }
    }
    pub fn info(cell: &'static std::sync::OnceLock<CString>, text: &str) -> *const c_char {
        cell.get_or_init(|| CString::new(text.replace('\0', " ")).unwrap_or_default()).as_ptr()
    }
}

/// Implements the complete vdsim C ABI for a type implementing Node.
macro_rules! export_node {
    ($node:ty, $info:expr) => {
        static VDSIM_NODE_INFO: std::sync::OnceLock<std::ffi::CString> = std::sync::OnceLock::new();

        #[no_mangle]
        pub extern "C" fn vdsim_abi_version() -> u32 {
            $crate::vdsim_node::ABI_VERSION
        }
        #[no_mangle]
        pub extern "C" fn vdsim_node_info() -> *const std::ffi::c_char {
            $crate::vdsim_node::ffi::info(&VDSIM_NODE_INFO, $info)
        }
        #[no_mangle]
        pub unsafe extern "C" fn vdsim_create(params: *const f64, n: usize) -> *mut std::ffi::c_void {
            $crate::vdsim_node::ffi::create::<$node>(params, n)
        }
        #[no_mangle]
        pub unsafe extern "C" fn vdsim_destroy(h: *mut std::ffi::c_void) {
            $crate::vdsim_node::ffi::destroy::<$node>(h)
        }
        #[no_mangle]
        pub unsafe extern "C" fn vdsim_reset(h: *mut std::ffi::c_void, dt: f64, seed: u64) -> i32 {
            $crate::vdsim_node::ffi::reset::<$node>(h, dt, seed)
        }
        #[no_mangle]
        pub unsafe extern "C" fn vdsim_step(h: *mut std::ffi::c_void, t: f64, n_in: usize, inp: *const *const f64,
                                            in_len: *const usize, n_out: usize, out: *const *mut f64,
                                            out_cap: *const usize, out_len: *mut usize) -> i32 {
            $crate::vdsim_node::ffi::step::<$node>(h, t, n_in, inp, in_len, n_out, out, out_cap, out_len)
        }
        #[no_mangle]
        pub unsafe extern "C" fn vdsim_fetch_outputs(h: *mut std::ffi::c_void, n_out: usize, out: *const *mut f64,
                                                     out_cap: *const usize, out_len: *mut usize) -> i32 {
            $crate::vdsim_node::ffi::fetch_outputs::<$node>(h, n_out, out, out_cap, out_len)
        }
        #[no_mangle]
        pub unsafe extern "C" fn vdsim_output(h: *mut std::ffi::c_void, t: f64, n_out: usize, out: *const *mut f64,
                                              out_cap: *const usize, out_len: *mut usize) -> i32 {
            $crate::vdsim_node::ffi::output::<$node>(h, t, n_out, out, out_cap, out_len)
        }
        #[no_mangle]
        pub unsafe extern "C" fn vdsim_update(h: *mut std::ffi::c_void, t: f64, dt: f64, n_in: usize,
                                              inp: *const *const f64, in_len: *const usize) -> i32 {
            $crate::vdsim_node::ffi::update::<$node>(h, t, dt, n_in, inp, in_len)
        }
        #[no_mangle]
        pub unsafe extern "C" fn vdsim_get_state(h: *mut std::ffi::c_void, buf: *mut f64, cap: usize) -> usize {
            $crate::vdsim_node::ffi::get_state::<$node>(h, buf, cap)
        }
        #[no_mangle]
        pub unsafe extern "C" fn vdsim_set_state(h: *mut std::ffi::c_void, buf: *const f64, n: usize) -> i32 {
            $crate::vdsim_node::ffi::set_state::<$node>(h, buf, n)
        }
        #[no_mangle]
        pub unsafe extern "C" fn vdsim_last_error(h: *mut std::ffi::c_void) -> *const std::ffi::c_char {
            $crate::vdsim_node::ffi::last_error::<$node>(h)
        }
    };
}
"""


def rust_module():
    recs = _records()
    text = _RUST_HEAD
    text = text.replace("@@ABI@@", str(ABI_VERSION)).replace("@@CODEC@@", str(T.CODEC_VERSION))
    text = text.replace("@@N_OBJECT_TYPES@@", str(len(T.OBJECT_TYPES)))
    text = text.replace("@@OBJECT_TYPES@@", ", ".join(f'"{n}"' for n in T.OBJECT_TYPES))
    text = text.replace("@@LAYOUT@@", _rust_layout(recs))
    text = text.replace("@@RECORDS@@", "\n\n".join(_rust_record(*r) for r in recs))
    lerp = "\n".join(f"            {f}: a.{f} + w * (b.{f} - a.{f}),"
                     for f in T.TRAJECTORY_FIELDS if f not in ("t", "theta"))
    return text.replace("@@LERP@@", lerp)


def write_headers(dest, cpp=True, rust=True):
    """Write vdsim_node.h and/or vdsim_node.rs into dest; returns the written paths."""
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    out = []
    if cpp:
        p = dest / "vdsim_node.h"
        p.write_text(cpp_header(), encoding="utf-8", newline="\n")
        out.append(p)
    if rust:
        p = dest / "vdsim_node.rs"
        p.write_text(rust_module(), encoding="utf-8", newline="\n")
        out.append(p)
    return out


def header_is_current(path):
    # True if a project's copy of the header equals the generated text
    path = Path(path)
    if not path.exists():
        return False
    gen = cpp_header() if path.suffix == ".h" else rust_module()
    return path.read_text(encoding="utf-8").replace("\r\n", "\n") == gen
