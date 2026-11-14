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
  waypoints?: WaypointPath;
}
export interface Waypoint { x: number; y: number; v_kmh: number; radius: number }
export interface WaypointPath { waypoints: Waypoint[]; ay_max?: number | null }
export interface TrajectoryData { name: string; length: number; s: number[]; x: number[]; y: number[]; psi: number[]; kappa: number[]; v: number[] }
export interface FrictionPatch { x_min: number; x_max: number; y_min: number; y_max: number; mu: number }
export interface SimulateResponse { run_id?: string; name: string; model: string; stop_reason: string; stop_code: string; simulated_time: number; wall_time: number; n_samples: number; kpis: Kpi[]; signals: Record<string, (number | null)[]> }
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
  planner_metrics?: PlannerMetrics; planner_config?: string; approach?: string; situations?: SituationSettings; dagger_rounds?: number[];
}
export interface PlannerMetrics {
  n_situations: number; cycles: number; network_share: number; acceptance: number; fallback_share: number; out_of_scope_share: number; infeasible_share: number;
  cost_ratio_median: number | null; cost_ratio_mean: number | null; cost_ratio_p90: number | null; within_5_percent_share: number | null; same_choice_share: number;
  closed_loop_cost_ratio: number | null; collisions: number; collisions_teacher: number; invalid_cycles: number; invalid_cycles_teacher: number;
  time_learned_ms: number; time_teacher_ms: number;
}
export interface DriveLog { t: number[]; x: number[]; y: number[]; v: number[]; cost: number[]; source?: string[] }
export interface DriveResult {
  learned: DriveLog; teacher: DriveLog; road: { x: number[]; y: number[]; left_x: number[]; left_y: number[]; right_x: number[]; right_y: number[] };
  objects: { id: number; length: number; width: number; x: number[]; y: number[]; psi: number }[];
  summary: { cycles: number; network_share: number; fallback_share: number; max_path_difference: number; cost_learned: number; cost_teacher: number;
    collision_learned: boolean; collision_teacher: boolean; time_learned_ms: number; time_teacher_ms: number };
}
export interface SituationSettings { curve_share: number; max_objects: number; speed_min: number; speed_max: number; lane_change_share: number }
export interface TrainRequest { kind?: "vehicle_dynamics" | "trajectory_planner"; planner_config?: string; approach?: "regression" | "classification" | "dagger"; situations?: SituationSettings | null; vehicle: string; teacher: "bicycle_nonlinear" | "bicycle_linear"; n_samples: number; hidden: number[]; epochs: number; learning_rate: number; seed: number; name: string }
export interface TrainJob { id: string; state: "queued" | "running" | "done" | "failed" | "cancelled"; phase: string; progress: number; history: { epoch: number; train: number; val: number }[]; model_id: string | null; error: string | null; created?: number; name?: string }
export interface Evaluation { maneuver: string; max_position_error: number; max_yaw_rate_error: number; wall_time: { physics: number; neural: number }; kpis: Record<string, { physics: number; neural: number }>; series: Record<string, number[]> }

export interface ParkRequest {
  vehicle?: string; kind: "parallel" | "perpendicular" | "angled"; entry: "reverse" | "forward"; side: "right" | "left";
  steering: "front" | "rear" | "counter" | "in_phase"; layout: "fwd" | "rwd" | "awd"; ratio?: number; max_rear_angle?: number;
  mu?: number; slope?: number; gap_length?: number; spot_width?: number; aisle_width?: number; angle_deg?: number; time_limit?: number; simulate?: boolean;
}
export interface ParkResponse {
  success: boolean; message: string; compute_time: number; nodes_expanded: number;
  geometry: { mode: string; min_radius: number; reference_from_rear_axle: number; max_front_deg: number; max_rear_deg: number; ratio: number };
  footprint: { front: number; rear: number; width: number; length: number };
  scenario: { kind: string; entry: string; side: string; start: number[]; goal: number[]; bounds: number[]; spot: number[][]; final_direction: number;
    obstacles: { kind: string; polygon: number[][] }[]; info: Record<string, number> };
  path?: { x: number[]; y: number[]; psi: number[]; direction: number[]; kappa: number[]; s: number[]; length: number; cusps: number; segments: { direction: number; length: number }[] };
  driven?: { success: boolean; message: string; t: number[]; x: number[]; y: number[]; psi: number[]; v: number[]; delta_f: number[]; delta_r: number[];
    e_lat: number[]; segment: number[]; traction_limited: boolean[]; kpis: Record<string, number | null> };
}
// ---- development environment (workbench, research, MATLAB, knowledge)
export interface ComponentParam { name: string; default: unknown; unit?: string; description?: string; label?: string; choices?: (string | number)[]; min?: number; max?: number; step?: number }
export interface ComponentOption { spec: string; label: string; version?: string; language?: string; params: ComponentParam[]; inputs: string[]; outputs: string[] }
export interface LayerInfo { layer: string; kind: string; default: string | null; components: ComponentOption[] }
export interface AdScenario { name: string; type: string; label: string; description: string; duration: number; seed: number }
export interface WorkbenchCatalog { scenarios: AdScenario[]; layers: LayerInfo[]; default_stack: Record<string, { component: string }>;
  kpi_info: Record<string, [string, string, string, string]>; limits: { max_duration: number } }
export interface LayerSpec { component: string; params?: Record<string, unknown> }
export interface Connection { from: string; to: string }
export interface RunRequest { scenario: string; seed?: number | null; duration?: number | null; stack?: Record<string, LayerSpec>; name?: string; connections?: Connection[] | null;
  friction?: number | null; wind_speed?: number | null }
export interface LiveActor { type: string; length: number; width: number; t: number; x: number; y: number; psi: number; v?: number }
export interface LiveFrame { t: number; t_end: number; stopped: boolean; stop_reason: string; row: Record<string, number | string | null>; objects: Record<string, LiveActor>;
  n_steps: number; n_snapshots: number; n_events: number; snapshot: PlannerSnapshot | null; events: ({ t: number; type: string } & Record<string, unknown>)[] }
export interface LiveSession { id: string; name: string; base_dt: number; road: RunResult["road"]; ego: { length: number; width: number }; frame: LiveFrame }
export interface SavedRun { format?: string; name?: string; meta: Record<string, unknown>; npz: string }
export interface MissionResult { passed: boolean; criteria: Record<string, { ok: boolean; detail: string }> }
export interface JobView { id: string; kind: string; name: string; state: "queued" | "running" | "done" | "failed" | "cancelled"; progress: number; error: string | null;
  created: number; finished: number | null; request: Record<string, unknown>;
  summary: { duration: number; n_snapshots: number; n_events: number; mission: MissionResult | null; stop_reason: string | null; wall_time: number | null } | null }
export interface RoadLane { id: string; type: string; center: number[][]; left: number[][]; right: number[][]; marking_left: string; marking_right: string }
export interface RunActor { type: string; length: number; width: number; t: number[]; x: number[]; y: number[]; psi: number[]; v?: number[] }
export interface SnapshotMeta { k: number; t: number; mode: string; fallback: boolean; reinitialized: boolean; n_candidates: number; compute_time: number; maneuver: string | null }
export interface RunResult {
  id: string; name: string; request: RunRequest; signals: Record<string, (number | null)[]>; objects: Record<string, RunActor>;
  road: { lanes: RoadLane[]; stop_lines: unknown[]; traffic_lights: unknown[]; parking: unknown[] };
  events: ({ t: number; type: string } & Record<string, unknown>)[]; kpis: Record<string, number | null>;
  profile: Record<string, { calls: number; mean: number; p95: number; max: number; total: number }>;
  mission: MissionResult | null; stop_reason: string | null; wall_time: number | null; duration: number; snapshots: SnapshotMeta[]; ego: { length: number; width: number };
}
export interface PlannerSnapshot {
  t: number; candidates_x: (number | null)[][]; candidates_y: (number | null)[][]; candidates_cost: (number | null)[]; candidates_status: number[];
  best_index: number; cost_terms: Record<string, number>; constraint_violations: Record<string, number>; n_candidates: number; n_checked: number; mode: string;
  modes: Record<string, Record<string, unknown>>; reinitialized: boolean; fallback: boolean; compute_time: number; info: Record<string, unknown>;
  trajectory: { t: number[]; x: number[]; y: number[]; v: number[] } | null; behavior: Record<string, unknown> | null;
  prediction: { id: number; t: number[]; x: number[]; y: number[] }[] | null; controller: Record<string, unknown> | null;
}
export interface StackGraph { nodes: { id: string; component: string; label: string; position: [number, number]; period?: number }[];
  connections: Connection[]; default_connections: Connection[]; issues: string[];
  ports: Record<string, { inputs: string[]; outputs: string[]; input_types: Record<string, { type: string; optional: boolean }>; output_types: Record<string, { type: string; optional: boolean }> }> }
export interface ExperimentRecord { label: string; ok: boolean; error: string | null; kpis: Record<string, number | null>; wall_time: number | null }
export interface ExperimentRequest { kind: "compare" | "sweep" | "monte_carlo"; base: RunRequest; layer?: string; variants?: Record<string, LayerSpec>;
  grid?: Record<string, (number | string | boolean)[]>; distributions?: Record<string, number[]>; n?: number; seed?: number }
export type ExperimentView = JobView & { records: ExperimentRecord[] };
export interface MatlabAnalysis { kind: string; functions: { name: string; inputs: string[]; outputs: string[]; line: number; variables: Record<string, { role: string; type: string; latex?: string }> }[];
  call_graph: unknown; builtins: string[]; equations: unknown[]; diagnostics: unknown[] }
export interface MatlabConversion { ok: boolean; files: Record<string, string>; report: unknown }
export interface Reference { type?: string; authors?: string[]; title?: string; year?: number; publisher?: string; journal?: string; url?: string; doi?: string }
export interface KnowledgeNode { id: string; type: string; label: string }
export interface KnowledgeExplain { info: Record<string, unknown>; markdown: string; nodes: KnowledgeNode[]; edges: { source: string; target: string; type: string }[] }

export interface ControlCatalog {
  controllers: { name: string; label: string; params: ComponentParam[]; doc: Record<string, unknown> }[];
  paths: Record<string, Record<string, number>>; plants: string[]; info_terms: string[];
}
export interface ControlRunRequest {
  controllers: { name: string; params?: Record<string, unknown>; label?: string }[]; path: string; path_params?: Record<string, number>; speed: number;
  plant?: string; mu?: number; actuator?: "ideal" | "realistic"; lateral_offset?: number; heading_offset_deg?: number; disturbance?: { t: number; duration: number; fy: number; mz?: number } | null; duration?: number;
}
export interface ControlKpis { max_e_n: number; rms_e_n: number; final_e_n: number; max_e_theta_deg: number; max_steer_deg: number; max_steer_rate_deg_s: number; max_ay: number;
  settled_after: number | null; compute_time_ms: number }
export interface ControlRun { name: string; label: string; params: Record<string, unknown>; stable: boolean; on_path: boolean; kpis: ControlKpis | null;
  signals: Record<string, (number | null)[]>; terms: Record<string, (number | null)[]>; active: string }
export interface ControlResult { path: { kind: string; x: number[]; y: number[]; kappa: number[]; s: number[]; maneuver_start: number }; speed: number; duration: number; plant: string; mu: number;
  vehicle: { wheelbase: number; length: number; width: number }; runs: ControlRun[] }
export interface ChatStatus { available: boolean; installed: boolean; credential: boolean; model: string }
export interface SimulationView { kind: "simulation"; request: Record<string, unknown>; model: string; stop_code: string; simulated_time: number; wall_time: number; kpis: Kpi[]; signals: Record<string, (number | null)[]> }
export interface PlanView {
  kind: "plan"; request: Record<string, unknown>; road: RoadGeometry | null; trajectory: { x: (number | null)[]; y: (number | null)[]; v: (number | null)[]; t: (number | null)[] };
  driven: { x: number[]; y: number[] }; obstacles: ObjectSpec[]; ego: { x: number; y: number; psi: number; vx: number }; valid: boolean; n_candidates: number; compute_time: number; cost: number | null;
}
export interface PredictionView { kind: "prediction"; request: Record<string, unknown>; objects: PredictedObject[] }
export type ParkingToolView = ParkResponse & { kind: "parking"; request: Record<string, unknown> };
export type ToolView = SimulationView | PlanView | PredictionView | ParkingToolView;
export type ChatEvent =
  | { event: "start"; data: { conversation_id: string; model: string } }
  | { event: "text"; data: { text: string } }
  | { event: "tool_use"; data: { id: string; name: string } }
  | { event: "tool_result"; data: { id: string; name: string; ok: boolean; input: Record<string, unknown>; view?: ToolView | null; error?: string; elapsed: number } }
  | { event: "done"; data: { conversation_id: string; stop_reason: string; model: string } }
  | { event: "error"; data: { code: string; message: string } };

// Server-sent events of POST /chat, parsed from the response body (EventSource cannot send a POST body).
async function* readEvents(body: ReadableStream<Uint8Array>): AsyncGenerator<ChatEvent> {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value ?? new Uint8Array(), { stream: !done });
    let cut: number;
    while ((cut = buffer.indexOf("\n\n")) >= 0) {
      const chunk = buffer.slice(0, cut);
      buffer = buffer.slice(cut + 2);
      let event = "message";
      const data: string[] = [];
      for (const line of chunk.split("\n")) {
        if (line.startsWith("event: ")) event = line.slice(7);
        else if (line.startsWith("data: ")) data.push(line.slice(6));
      }
      if (data.length) yield { event, data: JSON.parse(data.join("\n")) } as ChatEvent;
    }
    if (done) return;
  }
}

function errorKey(status: number): string {
  if (status === 401) return "errors.unauthorized";
  if (status === 403) return "errors.forbidden";
  if (status === 404) return "errors.notFound";
  if (status === 409) return "errors.conflict";
  if (status === 413) return "errors.tooLarge";
  if (status === 429) return "errors.rateLimited";
  if (status === 422) return "errors.invalid";
  if (status === 503) return "errors.busy";
  return "errors.server";
}

export function createClient(settings: Pick<Settings, "apiBase" | "apiKey">) {
  const base = settings.apiBase.replace(/\/+$/, "");
  const headers = (json: boolean) => ({ ...(json ? { "Content-Type": "application/json" } : {}), ...(settings.apiKey ? { "X-API-Key": settings.apiKey } : {}) });
  async function failure(res: Response): Promise<ApiError> {
    let detail = "";
    try {
      const j = (await res.json()) as { detail?: unknown };
      detail = typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail ?? "");
    } catch {
      detail = res.statusText;
    }
    return new ApiError(errorKey(res.status), res.status, detail);
  }
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
    trajectory: (body: { maneuver: string; vehicle: string; params?: Record<string, number | string | boolean>; max_points?: number }, s?: AbortSignal) =>
      request<{ name: string; length: number; x: number[]; y: number[]; psi: number[]; v: number[] }>("POST", "/trajectory", body, s),
    simulate: (body: SimulateRequest, s?: AbortSignal) => request<SimulateResponse>("POST", "/simulate", body, s),
    waypointTrajectory: (body: WaypointPath, s?: AbortSignal) => request<TrajectoryData>("POST", "/trajectory/waypoints", { ...body, max_points: 1500 }, s),
    waypointsFromManeuver: (body: { maneuver: string; vehicle: string; n_points: number }) => request<{ waypoints: Waypoint[] }>("POST", "/trajectory/waypoints/from-maneuver", body),
    async report(runIds: string[], format: "pdf" | "summary", title: string): Promise<Blob> {
      let res: Response;
      try {
        res = await fetch(`${base}/simulate/report`, { method: "POST", headers: headers(true), body: JSON.stringify({ run_ids: runIds, format, title }) });
      } catch (err) {
        throw new ApiError("errors.network", 0, String(err));
      }
      if (!res.ok) throw await failure(res);
      return res.blob();
    },
    explain: (body: PlanRequest, s?: AbortSignal) => request<ExplainResponse>("POST", "/plan/explain", body, s),
    predict: (body: { predictor: string; horizon: number; dt: number; objects: ObjectSpec[] }, s?: AbortSignal) => request<PredictResponse>("POST", "/predict", body, s),
    models: (s?: AbortSignal) => request<ModelMeta[]>("GET", "/models", undefined, s),
    model: (id: string, s?: AbortSignal) => request<ModelMeta>("GET", `/models/${encodeURIComponent(id)}`, undefined, s),
    deleteModel: (id: string) => request<void>("DELETE", `/models/${encodeURIComponent(id)}`),
    train: (body: TrainRequest) => request<TrainJob>("POST", "/models/train", body),
    job: (id: string, s?: AbortSignal) => request<TrainJob>("GET", `/models/jobs/${encodeURIComponent(id)}`, undefined, s),
    jobs: (s?: AbortSignal) => request<TrainJob[]>("GET", "/models/jobs", undefined, s),
    cancelJob: (id: string) => request<TrainJob>("POST", `/models/jobs/${encodeURIComponent(id)}/cancel`),
    connect: (body: { name: string; backend: "onnx" | "http"; onnx_base64?: string; url?: string; vehicle: string; kind?: "vehicle_dynamics" | "trajectory_planner" }) => request<ModelMeta>("POST", "/models/connect", body),
    drive: (id: string, body: { situation?: PlanRequest; seed?: number; cycles?: number }) => request<DriveResult>("POST", `/models/${encodeURIComponent(id)}/drive`, body),
    evaluate: (id: string, body: { maneuver: string; duration?: number }) => request<Evaluation>("POST", `/models/${encodeURIComponent(id)}/evaluate`, body),
    park: (body: ParkRequest, s?: AbortSignal) => request<ParkResponse>("POST", "/park", body, s),
    controlCatalog: (s?: AbortSignal) => request<ControlCatalog>("GET", "/control/catalog", undefined, s),
    controlRun: (body: ControlRunRequest, s?: AbortSignal) => request<ControlResult>("POST", "/control/run", body, s),
    workbenchCatalog: (s?: AbortSignal) => request<WorkbenchCatalog>("GET", "/workbench/catalog", undefined, s),
    stackGraph: (stack: Record<string, LayerSpec>, s?: AbortSignal, connections?: Connection[] | null) =>
      request<StackGraph>("POST", "/workbench/graph", { stack, ...(connections ? { connections } : {}) }, s),
    liveStart: (body: RunRequest) => request<LiveSession>("POST", "/workbench/live", body),
    liveAdvance: (id: string, body: { seconds?: number; steps?: number; known_snapshots: number }, s?: AbortSignal) =>
      request<LiveFrame>("POST", `/workbench/live/${encodeURIComponent(id)}/advance`, body, s),
    liveFinish: (id: string) => request<JobView>("POST", `/workbench/live/${encodeURIComponent(id)}/finish`),
    liveDelete: (id: string) => request<void>("DELETE", `/workbench/live/${encodeURIComponent(id)}`),
    importRun: (body: { meta: Record<string, unknown>; npz: string; name?: string }) => request<JobView>("POST", "/workbench/runs/import", body),
    startRun: (body: RunRequest) => request<JobView>("POST", "/workbench/runs", body),
    runs: (s?: AbortSignal) => request<JobView[]>("GET", "/workbench/runs", undefined, s),
    run: (id: string, s?: AbortSignal) => request<JobView>("GET", `/workbench/runs/${encodeURIComponent(id)}`, undefined, s),
    cancelRun: (id: string) => request<JobView>("POST", `/workbench/runs/${encodeURIComponent(id)}/cancel`),
    runResult: (id: string, s?: AbortSignal, maxPoints?: number) =>
      request<RunResult>("GET", `/workbench/runs/${encodeURIComponent(id)}/result${maxPoints ? `?max_points=${maxPoints}` : ""}`, undefined, s),
    runSnapshot: (id: string, k: number, s?: AbortSignal) => request<PlannerSnapshot>("GET", `/workbench/runs/${encodeURIComponent(id)}/snapshots/${k}`, undefined, s),
    runDownloadUrl: (id: string) => `${base}/workbench/runs/${encodeURIComponent(id)}/download`,
    runDownload: (id: string) => request<SavedRun>("GET", `/workbench/runs/${encodeURIComponent(id)}/download`),
    startExperiment: (body: ExperimentRequest) => request<ExperimentView>("POST", "/workbench/experiments", body),
    experiment: (id: string, s?: AbortSignal) => request<ExperimentView>("GET", `/workbench/experiments/${encodeURIComponent(id)}`, undefined, s),
    cancelExperiment: (id: string) => request<JobView>("POST", `/workbench/experiments/${encodeURIComponent(id)}/cancel`),
    matlabAnalyze: (source: string) => request<MatlabAnalysis>("POST", "/matlab/analyze", { source }),
    matlabConvert: (source: string, target: "python" | "c") => request<MatlabConversion>("POST", "/matlab/convert", { source, target }),
    references: (s?: AbortSignal) => request<Record<string, Reference>>("GET", "/knowledge/references", undefined, s),
    knowledgeNodes: (q: string, s?: AbortSignal) => request<KnowledgeNode[]>("GET", `/knowledge/nodes?limit=60&q=${encodeURIComponent(q)}`, undefined, s),
    knowledgeExplain: (id: string, s?: AbortSignal) => request<KnowledgeExplain>("GET", `/knowledge/explain?id=${encodeURIComponent(id)}`, undefined, s),
    componentDoc: (spec: string, s?: AbortSignal) => request<{ label: string; doc: Record<string, unknown> | null; params: ComponentParam[]; inputs: Record<string, unknown>; outputs: Record<string, unknown> }>("GET", `/knowledge/components/${spec}`, undefined, s),
    chatStatus: (s?: AbortSignal) => request<ChatStatus>("GET", "/chat/status", undefined, s),
    chatDelete: (id: string) => request<void>("DELETE", `/chat/${encodeURIComponent(id)}`),
    async *chat(body: { message: string; conversation_id?: string | null }, signal?: AbortSignal): AsyncGenerator<ChatEvent> {
      let res: Response;
      try {
        res = await fetch(`${base}/chat`, { method: "POST", signal, headers: headers(true), body: JSON.stringify(body) });
      } catch (err) {
        if ((err as Error).name === "AbortError") throw err;
        throw new ApiError("errors.network", 0, String(err));
      }
      if (!res.ok || !res.body) throw await failure(res);
      yield* readEvents(res.body);
    },
  };
}
export type Client = ReturnType<typeof createClient>;
