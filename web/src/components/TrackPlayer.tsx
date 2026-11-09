// Animated top view of a run: the vehicle outline moves along its path over time (play, pause, scrub, speed).
// "Follow" keeps the vehicle in view with a window of `followWidth` meters; "overview" shows the whole run.
import { memo, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import { fmt } from "../lib/format";
import { Icon } from "./Icon";
import type { Box, Polyline } from "./PathPlot";

const STROKE: Record<Polyline["kind"], { stroke: string; width: number; dash?: string; opacity?: number }> = {
  road: { stroke: "var(--me-text-subtle)", width: 1, dash: "6 6" },
  bound: { stroke: "var(--me-border-strong)", width: 1.5 },
  target: { stroke: "var(--me-accent)", width: 1, dash: "2 4", opacity: 0.8 },
  candidate: { stroke: "var(--me-chart-6)", width: 1, opacity: 0.35 },
  rejected: { stroke: "var(--me-text-subtle)", width: 1, opacity: 0.3 },
  collision: { stroke: "var(--me-danger)", width: 1, opacity: 0.45 },
  selected: { stroke: "var(--me-primary)", width: 2 },
  prediction: { stroke: "var(--me-warning)", width: 2, dash: "4 3" },
  physics: { stroke: "var(--me-chart-1)", width: 2.5 },
  neural: { stroke: "var(--me-chart-3)", width: 2, dash: "6 4" },
};

export interface Track {
  t: (number | null)[];
  x: (number | null)[];
  y: (number | null)[];
  psi: (number | null)[];          // vehicle heading, rad
  v?: (number | null)[];           // m/s, shown in the readout
  length: number;
  width: number;
  centerOffset?: number;           // geometric center ahead of (x, y), m
}

const pts = (x: (number | null)[], y: (number | null)[], n = x.length) => {
  const out: string[] = [];
  for (let i = 0; i < n; i++) {
    const a = x[i], b = y[i];
    if (a !== null && b !== null && Number.isFinite(a) && Number.isFinite(b)) out.push(`${a.toFixed(2)},${(-b).toFixed(2)}`);
  }
  return out.join(" ");
};

function sampleAt(track: Track, time: number) {
  const tt = track.t as number[];
  let lo = 0, hi = tt.length - 1;
  if (time <= tt[0]) hi = 0;
  else if (time >= tt[hi]) lo = hi;
  else {
    while (hi - lo > 1) { const mid = (lo + hi) >> 1; if (tt[mid] <= time) lo = mid; else hi = mid; }
  }
  const w = hi === lo ? 0 : (time - tt[lo]) / Math.max(tt[hi] - tt[lo], 1e-9);
  const f = (a: (number | null)[]) => ((a[lo] ?? 0) as number) + w * (((a[hi] ?? 0) as number) - ((a[lo] ?? 0) as number));
  let dpsi = ((track.psi[hi] ?? 0) as number) - ((track.psi[lo] ?? 0) as number);
  dpsi = Math.atan2(Math.sin(dpsi), Math.cos(dpsi));
  return { i: lo, x: f(track.x), y: f(track.y), psi: ((track.psi[lo] ?? 0) as number) + w * dpsi, v: track.v ? f(track.v) : null };
}

function TrackPlayerImpl({ track, lines = [], boxes = [], height = 300, followWidth = 40, ariaLabel, autoPlay = true }:
  { track: Track; lines?: Polyline[]; boxes?: Box[]; height?: number; followWidth?: number; ariaLabel: string; autoPlay?: boolean }) {
  const { t, i18n } = useTranslation("common");
  const tt = track.t as number[];
  const t0 = tt[0] ?? 0, t1 = tt[tt.length - 1] ?? 0;
  const reduced = typeof window !== "undefined" && window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
  const [time, setTime] = useState(t0);
  const [playing, setPlaying] = useState(autoPlay && !reduced);
  const [speed, setSpeed] = useState(1);
  const [follow, setFollow] = useState(true);
  const raf = useRef<number | null>(null);
  const last = useRef<number | null>(null);

  useEffect(() => { setTime(t0); last.current = null; }, [track, t0]);

  useEffect(() => {
    if (!playing) return;
    const tick = (now: number) => {
      const dt = last.current === null ? 0 : (now - last.current) / 1000;
      last.current = now;
      setTime((cur) => {
        const next = cur + dt * speed;
        if (next >= t1) { setPlaying(false); return t1; }
        return next;
      });
      raf.current = requestAnimationFrame(tick);
    };
    raf.current = requestAnimationFrame(tick);
    return () => { if (raf.current !== null) cancelAnimationFrame(raf.current); last.current = null; };
  }, [playing, speed, t1]);

  const cur = useMemo(() => sampleAt(track, time), [track, time]);
  const full = useMemo(() => {
    let xmin = Infinity, xmax = -Infinity, ymin = Infinity, ymax = -Infinity;
    const take = (x: number | null, y: number | null) => {
      if (x === null || y === null || !Number.isFinite(x) || !Number.isFinite(y)) return;
      xmin = Math.min(xmin, x); xmax = Math.max(xmax, x); ymin = Math.min(ymin, y); ymax = Math.max(ymax, y);
    };
    track.x.forEach((x, i) => take(x, track.y[i]));
    boxes.forEach((b) => take(b.x, b.y));
    const pad = Math.max(track.length, 4);
    if (!Number.isFinite(xmin)) return { x: -10, y: -10, w: 20, h: 20 };
    return { x: xmin - pad, y: -(ymax + pad), w: xmax - xmin + 2 * pad, h: ymax - ymin + 2 * pad };
  }, [track, boxes]);
  const aspectH = Math.max(height, 120);
  const view = useMemo(() => {
    if (!follow || full.w <= followWidth * 1.2) return full;
    // window of followWidth meters around the vehicle; the vertical extent follows the plot's aspect ratio
    const w = followWidth, h = Math.max(full.h, (followWidth * aspectH) / 900);
    return { x: cur.x - w / 2, y: -cur.y - h / 2, w, h };
  }, [follow, full, followWidth, cur.x, cur.y, aspectH]);

  const staticLayer = useMemo(() => (
    <g>
      {lines.map((l, i) => {
        const st = STROKE[l.kind];
        return <polyline key={i} points={pts(l.x, l.y)} fill="none" stroke={st.stroke} strokeWidth={st.width} strokeDasharray={st.dash}
          strokeOpacity={st.opacity ?? 1} vectorEffect="non-scaling-stroke" strokeLinejoin="round" strokeLinecap="round" />;
      })}
      {boxes.map((b, i) => (
        <rect key={i} x={b.x - b.length / 2} y={-b.y - b.width / 2} width={b.length} height={b.width} rx={0.3}
          transform={`rotate(${(-b.psi * 180) / Math.PI} ${b.x} ${-b.y})`} fill={b.kind === "ego" ? "var(--me-primary-strong)" : "var(--me-warning)"} fillOpacity={0.8} />
      ))}
      <polyline points={pts(track.x, track.y)} fill="none" stroke="var(--me-text-subtle)" strokeWidth={1} strokeDasharray="3 4"
        vectorEffect="non-scaling-stroke" />
    </g>
  ), [lines, boxes, track]);

  const off = track.centerOffset ?? 0;
  const cx = cur.x + off * Math.cos(cur.psi), cy = cur.y + off * Math.sin(cur.psi);
  const deg = (-cur.psi * 180) / Math.PI;
  const toggle = useCallback(() => {
    if (!playing && time >= t1) setTime(t0);
    last.current = null;
    setPlaying((p) => !p);
  }, [playing, time, t0, t1]);

  return (
    <div className="player">
      <svg className="chart player__view" viewBox={`${view.x} ${view.y} ${view.w} ${view.h}`} style={{ height }}
        preserveAspectRatio="xMidYMid meet" role="img" aria-label={ariaLabel}>
        {staticLayer}
        <polyline points={pts(track.x, track.y, cur.i + 1) + ` ${cur.x.toFixed(2)},${(-cur.y).toFixed(2)}`} fill="none"
          stroke="var(--me-primary)" strokeWidth={2.5} vectorEffect="non-scaling-stroke" strokeLinejoin="round" />
        <g transform={`rotate(${deg} ${cx} ${-cy})`}>
          <rect x={cx - track.length / 2} y={-cy - track.width / 2} width={track.length} height={track.width} rx={0.35}
            fill="var(--me-primary)" stroke="var(--me-surface)" strokeWidth={0.06} />
          {/* windshield marks the front */}
          <rect x={cx + track.length * 0.12} y={-cy - track.width * 0.38} width={track.length * 0.14} height={track.width * 0.76} rx={0.15}
            fill="var(--me-surface)" fillOpacity={0.75} />
        </g>
      </svg>
      <div className="player__controls">
        <button type="button" className="btn btn--secondary btn--sm btn--icon" onClick={toggle} aria-label={playing ? t("player.pause") : t("player.play")}
          title={playing ? t("player.pause") : t("player.play")}><Icon name={playing ? "pause" : "play"} size={16} /></button>
        <input type="range" className="player__scrub" min={t0} max={t1} step={(t1 - t0) / 1000 || 0.01} value={time}
          aria-label={t("player.time")} onChange={(e) => { setPlaying(false); setTime(Number(e.target.value)); }} />
        <span className="player__readout mono">{fmt(time, i18n.language, 3)} s{cur.v !== null ? ` · ${fmt(Math.abs(cur.v) * 3.6, i18n.language, 2)} km/h` : ""}</span>
        <select className="select select--sm" value={speed} aria-label={t("player.speed")} onChange={(e) => setSpeed(Number(e.target.value))}>
          {[0.5, 1, 2, 4, 8].map((s) => <option key={s} value={s}>{s}×</option>)}
        </select>
        <button type="button" className={`btn btn--sm ${follow ? "btn--secondary" : "btn--ghost"}`} aria-pressed={follow} onClick={() => setFollow((f) => !f)}>
          {t("player.follow")}</button>
      </div>
    </div>
  );
}

export const TrackPlayer = memo(TrackPlayerImpl);
