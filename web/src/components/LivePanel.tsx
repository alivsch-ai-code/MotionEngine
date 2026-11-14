// Live mode of the workbench: the stack runs on the server while the page plays, pauses or single-steps it.
// The view accumulates the frames into the shape of a run result, so the scene view is the same as for a
// finished run. (Desktop equivalent: live mode of the ADWorkbench with the telemetry panel.)
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import type { JobView, LiveFrame, LiveSession, PlannerSnapshot, RunActor, RunResult } from "../lib/api";
import { fmt, toDeg } from "../lib/format";
import { useClient } from "../lib/hooks";
import { ErrorAlert } from "./ErrorAlert";
import { Icon } from "./Icon";
import { SceneView } from "./SceneView";

const SIGNALS = ["t", "ego_x", "ego_y", "ego_psi", "ego_v"];
const SPEEDS = [0.25, 0.5, 1, 2];
const TICK = 0.1;      // s of wall time per request while playing
const TELEMETRY: [string, string, (v: number) => number, number][] = [
  ["ego_v", "km/h", (v) => v * 3.6, 2], ["ego_ax", "m/s²", (v) => v, 3], ["ego_ay", "m/s²", (v) => v, 3], ["delta", "°", toDeg, 3],
  ["e_n", "m", (v) => v, 3], ["e_t", "m", (v) => v, 3], ["target_speed", "km/h", (v) => v * 3.6, 2], ["plan_cost", "", (v) => v, 4], ["plan_time", "ms", (v) => v * 1000, 3],
];

interface Buffers { signals: Record<string, number[]>; objects: Record<string, RunActor> }

export function LivePanel({ session, lang, onFinished, onClosed }:
  { session: LiveSession; lang: string; onFinished: (job: JobView) => void; onClosed: () => void }) {
  const { t } = useTranslation(["app", "common"]);
  const client = useClient();
  const [frame, setFrame] = useState<LiveFrame>(session.frame);
  const [snapshot, setSnapshot] = useState<PlannerSnapshot | null>(session.frame.snapshot);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const [showCandidates, setShowCandidates] = useState(true);
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);
  const buffers = useRef<Buffers>({ signals: {}, objects: {} });
  const known = useRef(session.frame.n_snapshots);
  const pending = useRef(false);
  const done = useRef(false);

  const take = useCallback((f: LiveFrame) => {
    const b = buffers.current;
    if (typeof f.row.t === "number") {
      for (const key of SIGNALS) (b.signals[key] ??= []).push(typeof f.row[key] === "number" ? (f.row[key] as number) : 0);
    }
    for (const [id, o] of Object.entries(f.objects)) {
      const a = (b.objects[id] ??= { type: o.type, length: o.length, width: o.width, t: [], x: [], y: [], psi: [] });
      if (a.t[a.t.length - 1] !== o.t) { a.t.push(o.t); a.x.push(o.x); a.y.push(o.y); a.psi.push(o.psi); }
    }
    known.current = f.n_snapshots;
    if (f.snapshot) setSnapshot(f.snapshot);
    setFrame(f);
    if (f.stopped) setPlaying(false);
  }, []);
  useEffect(() => { buffers.current = { signals: {}, objects: {} }; take(session.frame); }, [session, take]);

  const advance = useCallback(async (body: { seconds?: number; steps?: number }) => {
    if (pending.current || done.current) return;
    pending.current = true;
    try {
      take(await client.liveAdvance(session.id, { ...body, known_snapshots: known.current }));
      setError(null);
    } catch (err) {
      setError(err);
      setPlaying(false);
    } finally {
      pending.current = false;
    }
  }, [client, session.id, take]);

  useEffect(() => {
    if (!playing) return;
    let stop = false;
    void (async () => {
      while (!stop) {
        const t0 = performance.now();
        await advance({ seconds: Math.max(TICK * speed, session.base_dt) });
        await new Promise((r) => window.setTimeout(r, Math.max(TICK * 1000 - (performance.now() - t0), 0)));
      }
    })();
    return () => { stop = true; };
  }, [playing, speed, advance, session.base_dt]);

  // a session that is left open is removed on the server
  useEffect(() => () => { if (!done.current) void client.liveDelete(session.id).catch(() => undefined); }, [client, session.id]);

  const finish = async () => {
    setPlaying(false);
    setBusy(true);
    try {
      while (pending.current) await new Promise((r) => window.setTimeout(r, 30));
      done.current = true;
      onFinished(await client.liveFinish(session.id));
    } catch (err) {
      done.current = false;
      setError(err);
    } finally {
      setBusy(false);
    }
  };
  const discard = () => { setPlaying(false); onClosed(); };

  const result = useMemo<RunResult>(() => ({
    id: session.id, name: session.name, request: { scenario: session.name }, signals: buffers.current.signals, objects: buffers.current.objects, road: session.road,
    events: [], kpis: {}, profile: {}, mission: null, stop_reason: null, wall_time: null, duration: frame.t, snapshots: [], ego: session.ego,
    // a new object per frame: the scene view compares the result by identity
  }), [session, frame]);
  const num = (key: string) => (typeof frame.row[key] === "number" ? (frame.row[key] as number) : null);
  const behavior = snapshot?.behavior as { maneuver?: string } | null | undefined;

  return (
    <>
      <ErrorAlert error={error} />
      <div className="row row--between">
        <div className="row">
          <span className={`badge ${frame.stopped ? "badge--warning" : playing ? "badge--success" : "badge--info"}`}>
            {frame.stopped ? t("live.stopped") : playing ? t("live.running") : t("live.paused")}</span>
          {frame.stopped && frame.stop_reason ? <span className="subtle">{t(`live.reasons.${reasonKey(frame.stop_reason)}`, { defaultValue: frame.stop_reason })}</span> : null}
        </div>
        <span className="subtle mono">{fmt(frame.t, lang, 4)} / {fmt(frame.t_end, lang, 3)} s · {t("live.steps", { n: frame.n_steps })}</span>
      </div>
      <div className="card"><div className="card__body player">
        <SceneView result={result} time={frame.t} snapshot={snapshot} showCandidates={showCandidates} ariaLabel={t("workbench.scene")} />
        <div className="progress" role="progressbar" aria-valuenow={Math.round((frame.t / Math.max(frame.t_end, 1e-9)) * 100)} aria-valuemin={0} aria-valuemax={100}>
          <span style={{ width: `${(frame.t / Math.max(frame.t_end, 1e-9)) * 100}%` }} /></div>
        <div className="player__controls">
          <button type="button" className="btn btn--primary btn--sm" disabled={frame.stopped || busy} onClick={() => setPlaying((p) => !p)}>
            <Icon name={playing ? "pause" : "play"} size={16} />{playing ? t("live.pause") : t("live.play")}</button>
          <button type="button" className="btn btn--secondary btn--sm" disabled={playing || frame.stopped || busy} onClick={() => void advance({ steps: 1 })}>{t("live.step")}</button>
          <button type="button" className="btn btn--secondary btn--sm" disabled={playing || frame.stopped || busy} onClick={() => void advance({ steps: 10 })}>{t("live.step10")}</button>
          <select className="select select--sm" value={speed} aria-label={t("common:player.speed")} onChange={(e) => setSpeed(Number(e.target.value))}>
            {SPEEDS.map((s) => <option key={s} value={s}>{s}×</option>)}</select>
          <button type="button" className={`btn btn--sm ${showCandidates ? "btn--secondary" : "btn--ghost"}`} aria-pressed={showCandidates}
            onClick={() => setShowCandidates((v) => !v)}>{t("workbench.candidates")}</button>
          <span style={{ flex: 1 }} />
          <button type="button" className="btn btn--secondary btn--sm" disabled={busy || frame.n_steps < 2} onClick={() => void finish()}>
            {busy ? <span className="spinner" /> : <Icon name="check" size={16} />}{t("live.finish")}</button>
          <button type="button" className="btn btn--ghost btn--sm" disabled={busy} onClick={discard}><Icon name="trash" size={16} />{t("live.discard")}</button>
        </div>
        <p className="subtle">{t("live.hint")}</p>
      </div></div>
      <div className="grid grid--2">
        <div className="card"><div className="card__header"><h2>{t("live.telemetry")}</h2></div><div className="card__body table-wrap"><table className="table"><tbody>
          {TELEMETRY.map(([key, unit, conv, digits]) => { const v = num(key); return (
            <tr key={key}><td>{t(`live.signals.${key}`)}</td><td className="num mono">{v === null ? "–" : fmt(conv(v), lang, digits)}</td><td className="subtle">{unit}</td></tr>); })}
        </tbody></table></div></div>
        <div className="card"><div className="card__header"><h2>{t("workbench.cycle")}</h2></div><div className="card__body table-wrap">
          {snapshot ? <table className="table"><tbody>
            <tr><td>{t("workbench.cycleTime")}</td><td className="num">{fmt(snapshot.t, lang, 3)} s</td></tr>
            <tr><td>{t("workbench.maneuver")}</td><td className="num">{String(behavior?.maneuver ?? "–")}</td></tr>
            <tr><td>{t("workbench.mode")}</td><td className="num">{snapshot.mode}</td></tr>
            <tr><td>{t("workbench.nCandidates")}</td><td className="num">{fmt(snapshot.n_candidates, lang)} / {fmt(snapshot.n_checked, lang)}</td></tr>
            <tr><td>{t("workbench.computeTime")}</td><td className="num">{fmt(snapshot.compute_time * 1000, lang, 3)} ms</td></tr>
            <tr><td>{t("workbench.flags")}</td><td className="num">{[snapshot.fallback ? t("workbench.fallback") : "", snapshot.reinitialized ? t("workbench.reinit") : ""].filter(Boolean).join(", ") || "–"}</td></tr>
          </tbody></table> : <p className="subtle">{t("live.noCycle")}</p>}
          {frame.events.length ? <div className="row" style={{ marginTop: "var(--me-space-2)" }}>{frame.events.slice(-6).map((e, i) => (
            <span key={i} className="badge badge--info">{fmt(e.t, lang, 3)} s · {e.type}</span>))}</div> : null}
        </div></div>
      </div>
    </>
  );
}

// language-neutral key of the library's stop reason
function reasonKey(reason: string) {
  if (reason.startsWith("Simulationsdauer")) return "duration";
  if (reason.startsWith("Kollision")) return "collision";
  if (reason.startsWith("Ziel")) return "goal";
  if (reason.startsWith("numerisch")) return "unstable";
  if (reason.startsWith("Fehler")) return "error";
  return "other";
}
