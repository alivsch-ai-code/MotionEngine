//! Pure-Pursuit tracking controller as vdsim custom node (Rust).
//!
//! Graph spec: "rust:examples/custom_nodes/rust/my_controller_node"
//! Same ports and algorithm as ../../python/my_controller_node.py (TrackingControllerBase):
//!     inputs  ego (EgoState), trajectory (PlannedTrajectory)
//!     outputs command (ControlCommand: steer_angle + accel), status (ControllerStatus)

#[macro_use]
mod vdsim_node;
use vdsim_node::*;

const INFO: &str = r#"{
  "name": "my_pure_pursuit_rust", "kind": "tracking_controller", "version": "1.0.0",
  "label": "Pure Pursuit (Beispiel, Rust)", "category": "Vehicle Control", "direct_feedthrough": true,
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
}"#;

const IN_EGO: usize = 0;
const IN_TRAJECTORY: usize = 1;
const OUT_COMMAND: usize = 0;
const OUT_STATUS: usize = 1;

/// same as Python: (a + pi) mod 2 pi - pi with floored modulo
fn wrap(a: f64) -> f64 {
    let pi = std::f64::consts::PI;
    (a + pi).rem_euclid(2.0 * pi) - pi
}

pub struct PurePursuit {
    lookahead_min: f64,
    lookahead_gain: f64,
    wheelbase: f64,
    cg_to_rear: f64,
    speed_gain: f64,
    max_steer: f64,
    calls: u64,
}

impl Node for PurePursuit {
    fn new(p: &[f64]) -> Self {
        Self {
            lookahead_min: param(p, 0, 4.0),
            lookahead_gain: param(p, 1, 0.8),
            wheelbase: param(p, 2, 2.8),
            cg_to_rear: param(p, 3, 1.4),
            speed_gain: param(p, 4, 1.0),
            max_steer: param(p, 5, 0.6),
            calls: 0,
        }
    }

    fn reset(&mut self, _dt: f64, _seed: u64) {
        self.calls = 0;
    }

    fn step(&mut self, t: f64, inputs: &Inputs, outputs: &mut Outputs) -> Result<(), String> {
        let Some(ego) = inputs.get::<EgoState>(IN_EGO) else { return Ok(()) };
        let traj: PlannedTrajectory = inputs.get_or_default(IN_TRAJECTORY);
        self.calls += 1;
        let (c, s) = (ego.psi.cos(), ego.psi.sin());
        let (xr, yr) = (ego.x - self.cg_to_rear * c, ego.y - self.cg_to_rear * s);
        if traj.is_empty() {
            let cmd = ControlCommand {
                t,
                steer_angle: Some(0.0),
                accel: Some(-self.speed_gain * ego.vx),
                direction: 1,
                ..Default::default()
            };
            outputs.set(OUT_COMMAND, &cmd);
            outputs.set(OUT_STATUS, &ControllerStatus { t, ..Default::default() });
            return Ok(());
        }
        let pts = &traj.points;
        let n = pts.len();
        let (mut i0, mut best) = (0usize, f64::INFINITY);
        for (i, q) in pts.iter().enumerate() {
            let (dx, dy) = (q.x - xr, q.y - yr);
            let d2 = dx * dx + dy * dy;
            if d2 < best {
                i0 = i;
                best = d2;
            }
        }
        let ld = self.lookahead_min + self.lookahead_gain * ego.vx.abs();
        let mut j = i0;
        while j < n - 1 {
            let (dx, dy) = (pts[j].x - xr, pts[j].y - yr);
            if (dx * dx + dy * dy).sqrt() >= ld {
                break;
            }
            j += 1;
        }
        let alpha = wrap((pts[j].y - yr).atan2(pts[j].x - xr) - ego.psi);
        let delta = (2.0 * self.wheelbase * alpha.sin()).atan2(ld).clamp(-self.max_steer, self.max_steer);
        let r = traj.sample(t);
        let (dx, dy) = (xr - pts[i0].x, yr - pts[i0].y);
        let (ct, st) = (pts[i0].theta.cos(), pts[i0].theta.sin());
        let status = ControllerStatus {
            t,
            e_t: dx * ct + dy * st,
            e_n: -dx * st + dy * ct,
            e_theta: wrap(ego.psi - pts[i0].theta),
            e_v: ego.vx - r.v,
            lookahead: ld,
            ..Default::default()
        };
        let cmd = ControlCommand {
            t,
            steer_angle: Some(delta),
            accel: Some(r.a + self.speed_gain * (r.v - ego.vx)),
            direction: traj.direction,
            ..Default::default()
        };
        outputs.set(OUT_COMMAND, &cmd);
        outputs.set(OUT_STATUS, &status);
        Ok(())
    }

    fn get_state(&self) -> Vec<f64> {
        vec![self.calls as f64]
    }

    fn set_state(&mut self, state: &[f64]) {
        if let Some(c) = state.first() {
            self.calls = *c as u64;
        }
    }
}

export_node!(PurePursuit, INFO);
