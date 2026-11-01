// Pure-Pursuit tracking controller as vdsim custom node (C++17).
//
// Graph spec: "cpp:examples/custom_nodes/cpp/my_controller_node"
// Same ports and algorithm as ../../python/my_controller_node.py (TrackingControllerBase):
//     inputs  ego (EgoState), trajectory (PlannedTrajectory)
//     outputs command (ControlCommand: steer_angle + accel), status (ControllerStatus)
#include <algorithm>

#include "vdsim_node.h"

static const char* INFO = R"json({
  "name": "my_pure_pursuit_cpp", "kind": "tracking_controller", "version": "1.0.0",
  "label": "Pure Pursuit (Beispiel, C++)", "category": "Vehicle Control", "direct_feedthrough": true,
  "summary": "Geometrischer Querregler (Pure Pursuit) mit P-Geschwindigkeitsregler",
  "inputs":  [{"name": "ego", "type": "EgoState"}, {"name": "trajectory", "type": "PlannedTrajectory"}],
  "outputs": [{"name": "command", "type": "ControlCommand"}, {"name": "status", "type": "ControllerStatus"}],
  "params": [
    {"name": "lookahead_min", "default": 4.0, "label": "Mindest-Vorausschau", "unit": "m", "min": 0.5},
    {"name": "lookahead_gain", "default": 0.8, "label": "Vorausschau je Geschwindigkeit", "unit": "s", "min": 0.0},
    {"name": "wheelbase", "default": 2.8, "label": "Radstand", "unit": "m", "min": 1.0},
    {"name": "cg_to_rear", "default": 1.4, "label": "Schwerpunkt - Hinterachse", "unit": "m", "min": 0.0},
    {"name": "speed_gain", "default": 1.0, "label": "Geschwindigkeitsverstärkung", "unit": "1/s", "min": 0.0},
    {"name": "max_steer", "default": 0.6, "label": "Max. Lenkwinkel", "unit": "rad", "min": 0.01}
  ]
})json";

enum Input : size_t { IN_EGO = 0, IN_TRAJECTORY = 1 };
enum Output : size_t { OUT_COMMAND = 0, OUT_STATUS = 1 };

// same as Python: (a + pi) mod 2 pi - pi with floored modulo
static double wrap(double a) {
  const double pi = 3.14159265358979323846;
  double m = std::fmod(a + pi, 2.0 * pi);
  if (m < 0.0) m += 2.0 * pi;
  return m - pi;
}

class PurePursuit : public vdsim::Node {
 public:
  PurePursuit(const double* p, size_t n)
      : lookahead_min_(vdsim::param(p, n, 0, 4.0)),
        lookahead_gain_(vdsim::param(p, n, 1, 0.8)),
        wheelbase_(vdsim::param(p, n, 2, 2.8)),
        cg_to_rear_(vdsim::param(p, n, 3, 1.4)),
        speed_gain_(vdsim::param(p, n, 4, 1.0)),
        max_steer_(vdsim::param(p, n, 5, 0.6)) {}

  void reset(double dt, uint64_t seed) override {
    (void)dt;
    (void)seed;
    calls_ = 0;
  }

  void step(double t, const vdsim::Inputs& in, vdsim::Outputs& out) override {
    if (!in.has(IN_EGO)) return;
    const vdsim::EgoState ego = in.get<vdsim::EgoState>(IN_EGO);
    const vdsim::PlannedTrajectory traj = in.get<vdsim::PlannedTrajectory>(IN_TRAJECTORY);
    ++calls_;
    const double c = std::cos(ego.psi), s = std::sin(ego.psi);
    const double xr = ego.x - cg_to_rear_ * c, yr = ego.y - cg_to_rear_ * s;
    vdsim::ControlCommand cmd;
    vdsim::ControllerStatus status;
    cmd.t = t;
    status.t = t;
    if (traj.empty()) {
      cmd.steer_angle = 0.0;
      cmd.accel = -speed_gain_ * ego.vx;
      cmd.direction = 1;
      out.set(OUT_COMMAND, cmd);
      out.set(OUT_STATUS, status);
      return;
    }
    const std::vector<vdsim::TrajectoryPoint>& pts = traj.points;
    const size_t n = pts.size();
    size_t i0 = 0;
    double best = std::numeric_limits<double>::infinity();
    for (size_t i = 0; i < n; ++i) {
      const double dx = pts[i].x - xr, dy = pts[i].y - yr;
      const double d2 = dx * dx + dy * dy;
      if (d2 < best) {
        i0 = i;
        best = d2;
      }
    }
    const double ld = lookahead_min_ + lookahead_gain_ * std::fabs(ego.vx);
    size_t j = i0;
    while (j < n - 1) {
      const double dx = pts[j].x - xr, dy = pts[j].y - yr;
      if (std::sqrt(dx * dx + dy * dy) >= ld) break;
      ++j;
    }
    const double alpha = wrap(std::atan2(pts[j].y - yr, pts[j].x - xr) - ego.psi);
    double delta = std::atan2(2.0 * wheelbase_ * std::sin(alpha), ld);
    delta = std::min(std::max(delta, -max_steer_), max_steer_);
    const vdsim::TrajectoryPoint r = traj.sample(t);
    const double dx = xr - pts[i0].x, dy = yr - pts[i0].y;
    const double ct = std::cos(pts[i0].theta), st = std::sin(pts[i0].theta);
    status.e_t = dx * ct + dy * st;
    status.e_n = -dx * st + dy * ct;
    status.e_theta = wrap(ego.psi - pts[i0].theta);
    status.e_v = ego.vx - r.v;
    status.lookahead = ld;
    cmd.steer_angle = delta;
    cmd.accel = r.a + speed_gain_ * (r.v - ego.vx);
    cmd.direction = traj.direction;
    out.set(OUT_COMMAND, cmd);
    out.set(OUT_STATUS, status);
  }

  std::vector<double> get_state() const override { return {static_cast<double>(calls_)}; }
  void set_state(const double* d, size_t n) override {
    if (n >= 1) calls_ = static_cast<long long>(d[0]);
  }

 private:
  double lookahead_min_, lookahead_gain_, wheelbase_, cg_to_rear_, speed_gain_, max_steer_;
  long long calls_ = 0;
};

VDSIM_EXPORT_NODE(PurePursuit, INFO)
