// Assistant: type what to simulate; Claude runs the tools of the API and answers with the results.
// Tool results arrive as structured views and are drawn with the same components as the other pages.
import { Fragment, memo, useCallback, useEffect, useMemo, useRef, useState, type FormEvent, type KeyboardEvent, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import { Chart } from "../components/Chart";
import { EmptyState } from "../components/EmptyState";
import { ErrorAlert } from "../components/ErrorAlert";
import { Icon } from "../components/Icon";
import { KpiTile } from "../components/KpiTile";
import { PageHeader } from "../components/PageHeader";
import { PathPlot, type Box, type Polyline } from "../components/PathPlot";
import { TrackPlayer, type Track } from "../components/TrackPlayer";
import type { ChatEvent, PlanView, PredictionView, SimulationView, ToolView } from "../lib/api";
import { kpiLabel, kpiValue, maneuverLabel, modelLabel } from "../lib/domain";
import { fmt } from "../lib/format";
import { useClient, useQuery } from "../lib/hooks";

interface ToolPart { type: "tool"; id: string; name: string; status: "running" | "done" | "error"; input?: Record<string, unknown>; view?: ToolView | null; error?: string; elapsed?: number }
type Part = { type: "text"; text: string } | ToolPart;
interface Turn { role: "user" | "assistant"; parts: Part[]; error?: { code: string; message: string } }

const SUGGESTIONS = ["dlc", "friction", "models", "plan"] as const;
const SIM_KPIS = ["max_ay", "max_yaw_rate", "max_beta", "max_lateral_error"];

export default function Chat() {
  const { t } = useTranslation(["app", "common"]);
  const client = useClient();
  const status = useQuery((s) => client.chatStatus(s), [client]);
  const [turns, setTurns] = useState<Turn[]>([]);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [requestError, setRequestError] = useState<unknown>(null);
  const conversation = useRef<string | null>(null);
  const abort = useRef<AbortController | null>(null);
  const end = useRef<HTMLDivElement>(null);

  useEffect(() => () => abort.current?.abort(), []);
  useEffect(() => { end.current?.scrollIntoView({ block: "end", behavior: "smooth" }); }, [turns]);

  // apply one server event to the last (assistant) turn
  const apply = useCallback((ev: ChatEvent) => {
    if (ev.event === "start") { conversation.current = ev.data.conversation_id; return; }
    setTurns((all) => {
      const next = all.slice();
      const last = { ...next[next.length - 1], parts: next[next.length - 1].parts.slice() };
      next[next.length - 1] = last;
      const parts = last.parts;
      if (ev.event === "text") {
        const tail = parts[parts.length - 1];
        if (tail?.type === "text") parts[parts.length - 1] = { type: "text", text: tail.text + ev.data.text };
        else parts.push({ type: "text", text: ev.data.text });
      } else if (ev.event === "tool_use") {
        parts.push({ type: "tool", id: ev.data.id, name: ev.data.name, status: "running" });
      } else if (ev.event === "tool_result") {
        const i = parts.findIndex((p) => p.type === "tool" && p.id === ev.data.id);
        const part: ToolPart = { type: "tool", id: ev.data.id, name: ev.data.name, status: ev.data.ok ? "done" : "error",
          input: ev.data.input, view: ev.data.view, error: ev.data.error, elapsed: ev.data.elapsed };
        if (i >= 0) parts[i] = part; else parts.push(part);
      } else if (ev.event === "error") {
        last.error = ev.data;
        // a failed turn is dropped by the server; tools still marked as running did not finish
        last.parts = parts.map((p) => (p.type === "tool" && p.status === "running" ? { ...p, status: "error" } : p));
      }
      return next;
    });
  }, []);

  const send = useCallback(async (text: string) => {
    const message = text.trim();
    if (!message || busy) return;
    setDraft("");
    setRequestError(null);
    setTurns((all) => [...all, { role: "user", parts: [{ type: "text", text: message }] }, { role: "assistant", parts: [] }]);
    setBusy(true);
    const ctrl = new AbortController();
    abort.current = ctrl;
    try {
      for await (const ev of client.chat({ message, conversation_id: conversation.current }, ctrl.signal)) apply(ev);
    } catch (err) {
      if ((err as Error).name !== "AbortError") {
        setRequestError(err);
        setTurns((all) => all.slice(0, -2));
        setDraft(message);
      }
    } finally {
      setBusy(false);
      abort.current = null;
    }
  }, [busy, client, apply]);

  const reset = () => {
    abort.current?.abort();
    if (conversation.current) client.chatDelete(conversation.current).catch(() => undefined);
    conversation.current = null;
    setTurns([]);
    setRequestError(null);
  };

  const onSubmit = (e: FormEvent) => { e.preventDefault(); void send(draft); };
  const onKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) { e.preventDefault(); void send(draft); }
  };

  const unavailable = status.data && !status.data.available;
  return (
    <div className="chat">
      <PageHeader title={t("chat.title")} description={t("chat.subtitle")}
        actions={turns.length ? <button type="button" className="btn btn--secondary" onClick={reset}><Icon name="plus" />{t("chat.newChat")}</button> : null} />
      {status.error ? <ErrorAlert error={status.error} /> : null}
      {unavailable ? (
        <div className="card"><EmptyState art="chat" title={t("chat.unavailable.title")}
          text={status.data?.installed ? t("chat.unavailable.credential") : t("chat.unavailable.package")}
          action={<Link className="btn btn--secondary" to="/app/settings">{t("chat.unavailable.action")}</Link>} /></div>
      ) : (
        <>
          <div className="chat__log" aria-live="polite" aria-busy={busy}>
            {turns.length === 0 ? (
              <div className="card"><EmptyState art="chat" title={t("chat.empty.title")} text={t("chat.empty.text")}
                action={<div className="chat__suggestions">{SUGGESTIONS.map((k) => (
                  <button key={k} type="button" className="btn btn--secondary btn--sm" onClick={() => void send(t(`chat.suggestions.${k}`))}>{t(`chat.suggestions.${k}`)}</button>
                ))}</div>} /></div>
            ) : turns.map((turn, i) => <TurnView key={i} turn={turn} pending={busy && i === turns.length - 1} />)}
            <div ref={end} className="chat__end" />
          </div>
          {requestError ? <ErrorAlert error={requestError} /> : null}
          <form className="chat__composer card" onSubmit={onSubmit}>
            <label htmlFor="chat-input" className="visually-hidden">{t("chat.inputLabel")}</label>
            <textarea id="chat-input" className="input chat__input" rows={2} value={draft} maxLength={4000}
              placeholder={t("chat.placeholder")} onChange={(e) => setDraft(e.target.value)} onKeyDown={onKey} disabled={!status.data} />
            <div className="row row--between">
              <span className="subtle chat__hint">{t("chat.hint", { model: status.data?.model ?? "" })}</span>
              {busy ? (
                <button type="button" className="btn btn--secondary" onClick={() => abort.current?.abort()}><Icon name="stop" />{t("chat.stop")}</button>
              ) : (
                <button type="submit" className="btn btn--primary" disabled={!draft.trim() || !status.data}><Icon name="send" />{t("chat.send")}</button>
              )}
            </div>
          </form>
        </>
      )}
    </div>
  );
}

const TurnView = memo(function TurnView({ turn, pending }: { turn: Turn; pending: boolean }) {
  const { t } = useTranslation("app");
  if (turn.role === "user") {
    return <div className="chat__turn chat__turn--user"><div className="chat__bubble">{(turn.parts[0] as { text: string }).text}</div></div>;
  }
  return (
    <div className="chat__turn chat__turn--assistant">
      <div className="chat__avatar" aria-hidden="true"><Icon name="chat" /></div>
      <div className="stack chat__content">
        {turn.parts.map((p, i) => (p.type === "text" ? <RichText key={i} text={p.text} /> : <ToolCard key={p.id} part={p} />))}
        {pending && turn.parts.length === 0 ? <div className="row subtle"><span className="spinner" aria-hidden="true" />{t("chat.thinking")}</div> : null}
        {turn.error ? (
          <div className="alert alert--danger" role="alert">
            <span style={{ color: "var(--me-danger)" }}><Icon name="alert" /></span>
            <div className="stack stack--sm"><strong>{t(`chat.errors.${turn.error.code}`, { defaultValue: t("chat.errors.other") })}</strong>
              <span className="subtle mono">{turn.error.message}</span></div>
          </div>
        ) : null}
      </div>
    </div>
  );
});

// Minimal Markdown for the assistant's text: paragraphs, bullet and numbered lists, **bold** and `code`.
// Rendered as React elements, never as HTML.
function inline(text: string): ReactNode[] {
  return text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g).map((s, i) => {
    if (s.startsWith("**") && s.endsWith("**") && s.length > 4) return <strong key={i}>{s.slice(2, -2)}</strong>;
    if (s.startsWith("`") && s.endsWith("`") && s.length > 2) return <code key={i} className="mono">{s.slice(1, -1)}</code>;
    return <Fragment key={i}>{s}</Fragment>;
  });
}

const RichText = memo(function RichText({ text }: { text: string }) {
  const blocks = useMemo(() => {
    const out: { kind: "p" | "ul" | "ol"; lines: string[] }[] = [];
    for (const raw of text.split("\n")) {
      const line = raw.trimEnd();
      const bullet = /^\s*[-*•]\s+(.*)$/.exec(line);
      const numbered = /^\s*\d+[.)]\s+(.*)$/.exec(line);
      const kind = bullet ? "ul" : numbered ? "ol" : "p";
      const content = bullet?.[1] ?? numbered?.[1] ?? line.replace(/^#+\s*/, "");
      if (!line.trim()) { out.push({ kind: "p", lines: [] }); continue; }
      const last = out[out.length - 1];
      if (last && last.kind === kind && (kind !== "p" || last.lines.length)) last.lines.push(content);
      else out.push({ kind, lines: [content] });
    }
    return out.filter((b) => b.lines.length);
  }, [text]);
  return (
    <div className="chat__text">
      {blocks.map((b, i) => b.kind === "p"
        ? <p key={i}>{b.lines.map((l, j) => <Fragment key={j}>{j ? <br /> : null}{inline(l)}</Fragment>)}</p>
        : b.kind === "ul" ? <ul key={i}>{b.lines.map((l, j) => <li key={j}>{inline(l)}</li>)}</ul>
          : <ol key={i}>{b.lines.map((l, j) => <li key={j}>{inline(l)}</li>)}</ol>)}
    </div>
  );
});

const ToolCard = memo(function ToolCard({ part }: { part: ToolPart }) {
  const { t, i18n } = useTranslation(["app", "common", "domain"]);
  const view = part.view;
  return (
    <section className="card chat__tool" aria-label={t(`chat.tools.${part.name}`, { defaultValue: part.name })}>
      <div className="card__header">
        <div className="row">
          <span className={`chat__tool-icon chat__tool-icon--${part.status}`}>
            {part.status === "running" ? <span className="spinner" aria-hidden="true" /> : <Icon name={part.status === "done" ? "check" : "alert"} />}
          </span>
          <strong>{t(`chat.tools.${part.name}`, { defaultValue: part.name })}</strong>
          {view?.kind === "simulation" ? <span className="subtle">{toolSubtitle(t, view)}</span> : null}
        </div>
        {part.elapsed !== undefined ? <span className="subtle">{t("chat.elapsed", { s: fmt(part.elapsed, i18n.language, 2) })}</span> : null}
      </div>
      <div className="card__body stack">
        {part.status === "error" && part.error ? <p className="mono subtle">{part.error}</p> : null}
        {view?.kind === "simulation" ? <SimulationResult view={view} /> : null}
        {view?.kind === "plan" ? <PlanResult view={view} /> : null}
        {view?.kind === "prediction" ? <PredictionResult view={view} /> : null}
        {part.input && Object.keys(part.input).length ? (
          <details className="chat__input-details">
            <summary>{t("chat.parameters")}</summary>
            <pre className="mono">{JSON.stringify(part.input, null, 2)}</pre>
          </details>
        ) : null}
      </div>
    </section>
  );
});

function toolSubtitle(t: ReturnType<typeof useTranslation>["t"], view: SimulationView) {
  const maneuver = typeof view.request.maneuver === "string" ? maneuverLabel(t, view.request.maneuver)
    : typeof view.request.scenario === "string" ? view.request.scenario : null;
  return [maneuver, modelLabel(t, view.model)].filter(Boolean).join(" · ");
}

function SimulationResult({ view }: { view: SimulationView }) {
  const { t, i18n } = useTranslation(["app", "common", "domain"]);
  const s = view.signals;
  const kpis = SIM_KPIS.map((k) => view.kpis.find((x) => x.key === k)).filter((k): k is NonNullable<typeof k> => Boolean(k));
  const lines = useMemo<Polyline[]>(() => [{ x: s.x ?? [], y: s.y ?? [], kind: "physics" }], [s]);
  const track = useMemo<Track>(() => ({ t: s.t ?? [], x: s.x ?? [], y: s.y ?? [], psi: s.psi ?? [], v: s.vx ?? [], length: 4.8, width: 1.85 }), [s]);
  const series = useMemo(() => [{ label: t("simulate.series.ay"), values: s.ay ?? [] }], [s, t]);
  return (
    <>
      <div className="grid grid--4">
        {kpis.map((k) => <KpiTile key={k.key} label={kpiLabel(t, k)} value={kpiValue(t, k)} unit={k.unit} lang={i18n.language} badge={k.rating as "ok" | "warn" | "fail" | ""} />)}
      </div>
      <div className="grid grid--2">
        {track.psi.length ? <TrackPlayer track={track} height={200} followWidth={30} autoPlay={false} ariaLabel={t("chat.drivenPath")} />
          : <PathPlot lines={lines} height={200} ariaLabel={t("chat.drivenPath")} />}
        <Chart x={s.t ?? []} series={series} xLabel="t [s]" yLabel="a_y [m/s²]" height={200} ariaLabel={t("simulate.series.ay")} />
      </div>
    </>
  );
}

function PlanResult({ view }: { view: PlanView }) {
  const { t, i18n } = useTranslation(["app", "common"]);
  const { lines, boxes } = useMemo(() => {
    const r = view.road;
    const l: Polyline[] = r ? [
      { x: r.left_x, y: r.left_y, kind: "bound" }, { x: r.right_x, y: r.right_y, kind: "bound" },
      { x: r.target_x, y: r.target_y, kind: "target" },
    ] : [];
    if (view.driven.x.length > 1) l.push({ x: view.driven.x, y: view.driven.y, kind: "physics" });
    l.push({ x: view.trajectory.x, y: view.trajectory.y, kind: "selected" });
    const b: Box[] = [{ x: view.ego.x, y: view.ego.y, psi: view.ego.psi, length: 4.6, width: 1.9, kind: "ego" },
      ...view.obstacles.map((o) => ({ x: o.x, y: o.y, psi: o.psi ?? 0, length: o.length ?? 4.5, width: o.width ?? 1.8, kind: "object" as const }))];
    return { lines: l, boxes: b };
  }, [view]);
  const xs = [...view.trajectory.x, ...view.driven.x].filter((v): v is number => v !== null);
  const focus = xs.length ? { xmin: Math.min(...xs) - 10, xmax: Math.max(...xs) + 10 } : undefined;
  return (
    <>
      <div className="row subtle chat__facts">
        <span className={`badge ${view.valid ? "badge--success" : "badge--danger"}`}>{view.valid ? t("chat.plan.valid") : t("chat.plan.invalid")}</span>
        <span>{t("chat.plan.candidates", { n: view.n_candidates })}</span>
        <span>{t("chat.plan.computeTime", { ms: fmt(view.compute_time * 1000, i18n.language, 3) })}</span>
      </div>
      <PathPlot lines={lines} boxes={boxes} height={220} focus={focus} ariaLabel={t("chat.plan.plot")} />
    </>
  );
}

function PredictionResult({ view }: { view: PredictionView }) {
  const { t } = useTranslation("app");
  const { lines, boxes } = useMemo(() => ({
    lines: view.objects.map<Polyline>((o) => ({ x: o.x, y: o.y, kind: "prediction" })),
    boxes: view.objects.map<Box>((o) => ({ x: o.x[0], y: o.y[0], psi: o.psi[0], length: o.length, width: o.width, kind: "object" })),
  }), [view]);
  return <PathPlot lines={lines} boxes={boxes} height={220} ariaLabel={t("chat.predictionPlot")} />;
}
