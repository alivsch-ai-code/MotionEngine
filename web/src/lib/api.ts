// Typed client of the MotionEngine REST service (vdsim.service). Errors carry an i18n key.
import type { Settings } from "./settings";

export class ApiError extends Error {
  constructor(public readonly key: string, public readonly status: number, public readonly detail: string) {
    super(detail || key);
  }
}

export interface Health { status: string; name: string; version: string; uptime_s: number }
export interface Catalog { presets: string[]; vehicle_models: string[]; tire_models: string[]; lateral_controllers: string[]; longitudinal_controllers: string[] }
export interface ParameterInfo { key: string; value: number | string | boolean | number[] | null; unit: string; min: number | null; max: number | null }
export interface SpeedAnalysis { speed: number; yaw_gain: number; ay_gain: number; natural_frequency: number; damping: number }
export interface VehicleDetail {
  name: string;
  schema: ParameterInfo[];
  analysis: { understeer_gradient: number; understeer_gradient_deg_per_g: number; characteristic_speed: number | null; critical_speed: number | null; cornering_stiffness_front: number; cornering_stiffness_rear: number; per_speed: SpeedAnalysis[] };
}
export interface ManeuverInfo { label: string; category: string; description: string; params: Record<string, [string, string]> }
export interface Kpi { key: string; label: string; value: number | string | null; value_code: string | null; unit: string; group: string; group_code: string; rating: string }
export interface SimulateRequest {
  vehicle?: string; model?: string; maneuver?: string; maneuver_params?: Record<string, number | string | boolean>;
  lateral_controller?: string; longitudinal_controller?: string; duration?: number; dt_control?: number;
  solver?: "euler" | "heun" | "rk4" | "adaptive"; environment?: Record<string, unknown>;
  vehicle_overrides?: Record<string, number | string | boolean>; signals?: string[]; max_points?: number;
}
export interface SimulateResponse { name: string; model: string; stop_reason: string; stop_code: string; simulated_time: number; wall_time: number; n_samples: number; kpis: Kpi[]; signals: Record<string, (number | null)[]> }
export interface ObjectSpec { id: number; type?: string; x: number; y: number; psi?: number; v: number; a?: number; yaw_rate?: number; length?: number; width?: number }
export interface RoadSegment { kind: "straight" | "arc"; length: number; curvature?: number }
export interface PlanRequest {
  config?: string; vehicle?: string; road?: RoadSegment[]; ego?: { x?: number; y?: number; psi?: number; vx: number; ax?: number };
  target_speed?: number; target_offset?: number; d_min?: number; d_max?: number; stop_at?: number | null; obstacles?: ObjectSpec[]; cycles?: number; max_points?: number;
}
export interface RoadGeometry { x: number[]; y: number[]; left_x: number[]; left_y: number[]; right_x: number[]; right_y: number[]; target_x: number[]; target_y: number[] }
export interface ExplainStep { id: string; quantities: Record<string, unknown>; formulas: string[] }
export interface Candidate { x: (number | null)[]; y: (number | null)[]; s: (number | null)[]; d: (number | null)[]; status: number; cost: number | null; selected: boolean }
export interface ExplainResponse { road: RoadGeometry; obstacles: ObjectSpec[]; steps: ExplainStep[]; series: Record<string, (number | null)[]>; candidates: Candidate[]; weights: Record<string, unknown>; compute_time: number }
export interface PredictedObject { id: number; type: string; length: number; width: number; t: number[]; x: number[]; y: number[]; psi: number[]; v: number[] }
export interface PredictResponse { t0: number; predictor: string; objects: PredictedObject[] }
export interface Metric { rmse: number; max_abs: number; r2: number | null }
export interface ModelMeta {
  id: string; name: string; backend: "mlp" | "onnx" | "http"; kind: string; vehicle: string; teacher?: string; created: number;
  vehicle_model: string; hidden?: number[]; n_samples?: number; epochs_run?: number; n_parameters?: number;
  time_total_s?: number; test_metrics?: Record<string, Metric>; history?: { epoch: number; train: number; val: number }[]; url?: string;
}
export interface TrainRequest { vehicle: string; teacher: "bicycle_nonlinear" | "bicycle_linear"; n_samples: number; hidden: number[]; epochs: number; learning_rate: number; seed: number; name: string }
export interface TrainJob { id: string; state: "queued" | "running" | "done" | "failed" | "cancelled"; phase: string; progress: number; history: { epoch: number; train: number; val: number }[]; model_id: string | null; error: string | null }
export interface Evaluation { maneuver: string; max_position_error: number; max_yaw_rate_error: number; wall_time: { physics: number; neural: number }; kpis: Record<string, { physics: number; neural: number }>; series: Record<string, number[]> }

function errorKey(status: number): string {
  if (status === 401) return "errors.unauthorized";
  if (status === 403) return "errors.forbidden";
  if (status === 404) return "errors.notFound";
  if (status === 409) return "errors.conflict";
  if (status === 413) return "errors.tooLarge";
  if (status === 422) return "errors.invalid";
  if (status === 503) return "errors.busy";
  return "errors.server";
}

export function createClient(settings: Pick<Settings, "apiBase" | "apiKey">) {
  const base = settings.apiBase.replace(/\/+$/, "");
  async function request<T>(method: string, path: string, body?: unknown, signal?: AbortSignal): Promise<T> {
    let res: Response;
    try {
      res = await fetch(`${base}${path}`, {
        method,
        signal,
        headers: { ...(body !== undefined ? { "Content-Type": "application/json" } : {}), ...(settings.apiKey ? { "X-API-Key": settings.apiKey } : {}) },
        body: body !== undefined ? JSON.stringify(body) : undefined,
      });
    } catch (err) {
      if ((err as Error).name === "AbortError") throw err;
      throw new ApiError("errors.network", 0, String(err));
    }
    if (!res.ok) {
      let detail = "";
      try {
        const j = (await res.json()) as { detail?: unknown };
        detail = typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail ?? "");
      } catch {
        detail = res.statusText;
      }
      throw new ApiError(errorKey(res.status), res.status, detail);
    }
    if (res.status === 204) return undefined as T;
    return (await res.json()) as T;
  }
  return {
    health: (s?: AbortSignal) => request<Health>("GET", "/health", undefined, s),
    catalog: (s?: AbortSignal) => request<Catalog>("GET", "/vehicle", undefined, s),
    vehicle: (name: string, s?: AbortSignal) => request<VehicleDetail>("GET", `/vehicle/${encodeURIComponent(name)}`, undefined, s),
    maneuvers: (s?: AbortSignal) => request<Record<string, ManeuverInfo>>("GET", "/trajectory/maneuvers", undefined, s),
    simulate: (body: SimulateRequest, s?: AbortSignal) => request<SimulateResponse>("POST", "/simulate", body, s),
    explain: (body: PlanRequest, s?: AbortSignal) => request<ExplainResponse>("POST", "/plan/explain", body, s),
    predict: (body: { predictor: string; horizon: number; dt: number; objects: ObjectSpec[] }, s?: AbortSignal) => request<PredictResponse>("POST", "/predict", body, s),
    models: (s?: AbortSignal) => request<ModelMeta[]>("GET", "/models", undefined, s),
    model: (id: string, s?: AbortSignal) => request<ModelMeta>("GET", `/models/${encodeURIComponent(id)}`, undefined, s),
    deleteModel: (id: string) => request<void>("DELETE", `/models/${encodeURIComponent(id)}`),
    train: (body: TrainRequest) => request<TrainJob>("POST", "/models/train", body),
    job: (id: string, s?: AbortSignal) => request<TrainJob>("GET", `/models/jobs/${encodeURIComponent(id)}`, undefined, s),
    cancelJob: (id: string) => request<TrainJob>("POST", `/models/jobs/${encodeURIComponent(id)}/cancel`),
    connect: (body: { name: string; backend: "onnx" | "http"; onnx_base64?: string; url?: string; vehicle: string }) => request<ModelMeta>("POST", "/models/connect", body),
    evaluate: (id: string, body: { maneuver: string; duration?: number }) => request<Evaluation>("POST", `/models/${encodeURIComponent(id)}/evaluate`, body),
  };
}
export type Client = ReturnType<typeof createClient>;
