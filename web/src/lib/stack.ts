// The AD stack the user is editing: component and parameter overrides per layer. Shared by the workbench,
// the research page and the architecture view (session storage).
import type { Connection, LayerSpec } from "./api";
import { usePersistentState } from "./hooks";

export type StackEdit = Record<string, { component: string; paramsText: string }>;

export function useStack(): [StackEdit, (s: StackEdit) => void] {
  return usePersistentState<StackEdit>("me.workbench.stack", {});
}

// Parses the JSON parameter overrides; returns the layer whose JSON is invalid instead of throwing.
export function stackSpecs(stack: StackEdit): { specs: Record<string, LayerSpec>; invalid: string | null } {
  const specs: Record<string, LayerSpec> = {};
  for (const [layer, edit] of Object.entries(stack)) {
    if (!edit.component) continue;
    let params: Record<string, unknown> | undefined;
    if (edit.paramsText.trim()) {
      try {
        const parsed: unknown = JSON.parse(edit.paramsText);
        if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) return { specs, invalid: layer };
        params = parsed as Record<string, unknown>;
      } catch {
        return { specs, invalid: layer };
      }
    }
    specs[layer] = { component: edit.component, ...(params && Object.keys(params).length ? { params } : {}) };
  }
  return { specs, invalid: null };
}

// Edited connections of the stack graph (null = the default wiring). Shared like the stack.
export function useConnections(): [Connection[] | null, (c: Connection[] | null) => void] {
  return usePersistentState<Connection[] | null>("me.workbench.connections", null);
}

export function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = filename; a.click();
  URL.revokeObjectURL(url);
}

export function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(reader.error);
    reader.onload = () => resolve(String(reader.result).split(",")[1] ?? "");
    reader.readAsDataURL(file);
  });
}

// Conditions of a stack run: how close the plant and the sensors are to a real vehicle. A preset fills the
// plant and perception layers unless the user configured them, and sets the friction coefficient.
export const CONDITIONS = ["ideal", "realistic", "wet", "harsh"] as const;
export type Conditions = (typeof CONDITIONS)[number];
const SENSOR = { latency: 0.1, pos_sigma: 0.15, vel_sigma: 0.3, ego_pos_sigma: 0.05, ego_heading_sigma_deg: 0.2 };
const ACTUATOR = { steering: { dead_time: 0.03, tau: 0.05, rate_limit: 0.6 }, drive_tau: 0.2, brake_tau: 0.1 };
const PRESETS: Record<Conditions, { plant?: string; sensor?: Record<string, number>; friction?: number }> = {
  ideal: {},
  realistic: { plant: "double_track", sensor: SENSOR, friction: 1.0 },
  wet: { plant: "double_track", sensor: SENSOR, friction: 0.5 },
  harsh: { plant: "double_track", sensor: { latency: 0.2, pos_sigma: 0.3, vel_sigma: 0.5, ego_pos_sigma: 0.1, ego_heading_sigma_deg: 0.5 }, friction: 0.3 },
};
export function applyConditions(specs: Record<string, LayerSpec>, conditions: Conditions): { stack: Record<string, LayerSpec>; friction: number | null } {
  const preset = PRESETS[conditions] ?? {};
  const stack = { ...specs };
  if (preset.plant && !stack.plant) stack.plant = { component: "vehicle_plant/vehicle_model", params: { model: preset.plant } };
  if (preset.sensor && !stack.perception) stack.perception = { component: "perception/object_sensor", params: preset.sensor };
  if (preset.plant && !stack.actuators) stack.actuators = { component: "actuator/steering_powertrain", params: ACTUATOR };
  return { stack, friction: preset.friction ?? null };
}
