// Finished vehicle-dynamics runs of this page session, for the run comparison and the report. Kept in memory
// (signals are too large for session storage); the last run is restored by the Simulate page itself.
import { useSyncExternalStore } from "react";

import type { FrictionPatch, SimulateRequest, SimulateResponse, Waypoint } from "./api";

export interface SimRun { key: string; label: string; at: number; request: SimulateRequest | null; data: SimulateResponse; loaded?: boolean }
export const MAX_RUNS = 8;

let runs: SimRun[] = [];
const listeners = new Set<() => void>();
const emit = () => listeners.forEach((l) => l());

export function addRun(run: Omit<SimRun, "key">) {
  const key = run.data.run_id || `local-${run.at}-${Math.round(Math.random() * 1e6)}`;
  if (runs.some((r) => r.key === key)) return key;
  runs = [...runs, { ...run, key }].slice(-MAX_RUNS);
  emit();
  return key;
}
export function removeRuns(keys: string[]) {
  runs = runs.filter((r) => !keys.includes(r.key));
  emit();
}
export function useRuns(): SimRun[] {
  return useSyncExternalStore((l) => { listeners.add(l); return () => listeners.delete(l); }, () => runs);
}

// Trajectory of the editor that the Simulate page drives instead of a maneuver (session storage key).
export const APPLIED_KEY = "me.editor.applied";
export interface AppliedTrajectory { waypoints: Waypoint[] | null; ay_max: number; patches: FrictionPatch[] }

// linear interpolation of a signal onto a time grid (runs have different sample times)
export function resample(t: (number | null)[], v: (number | null)[], grid: number[]): (number | null)[] {
  const out: (number | null)[] = [];
  let j = 0;
  const n = Math.min(t.length, v.length);
  for (const g of grid) {
    while (j < n - 2 && (t[j + 1] ?? Infinity) < g) j++;
    const t0 = t[j], t1 = t[j + 1], v0 = v[j], v1 = v[j + 1];
    if (t0 === null || t0 === undefined || v0 === null || v0 === undefined || g < t0 - 1e-9) out.push(null);
    else if (t1 === null || t1 === undefined || v1 === null || v1 === undefined || g > t1 + 1e-9) out.push(Math.abs(g - t0) < 1e-9 ? v0 : null);
    else out.push(v0 + ((v1 - v0) * (g - t0)) / Math.max(t1 - t0, 1e-12));
  }
  return out;
}
