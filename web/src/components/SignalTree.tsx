// One signal value as a tree: numbers and texts as they are, objects as collapsible groups, long arrays as
// size, range and first elements (the server reduces them, see signal_tree in vdsim/ad/live.py).
import { useTranslation } from "react-i18next";

import type { SignalValue } from "../lib/api";
import { fmt } from "../lib/format";

const scalar = (v: SignalValue, lang: string) => (v === null ? "–" : typeof v === "number" ? fmt(Math.abs(v) < 1e-9 ? 0 : v, lang, 5) : String(v));
const flat = (v: SignalValue) => v === null || typeof v !== "object";

export function SignalTree({ value, lang, depth = 0 }: { value: SignalValue; lang: string; depth?: number }) {
  const { t } = useTranslation(["app"]);
  if (flat(value)) return <span className="mono">{scalar(value, lang)}</span>;
  if (Array.isArray(value)) {
    if (value.every(flat)) return <span className="mono">[{value.map((v) => scalar(v, lang)).join("; ")}]</span>;
    return <div className="signal-tree">{value.map((v, i) => <div key={i} className="signal-tree__row"><span className="subtle mono">{i}</span><SignalTree value={v} lang={lang} depth={depth + 1} /></div>)}</div>;
  }
  if (value._kind === "array") {
    const first = Array.isArray(value.first) ? value.first : [];
    return <span className="mono">{t("live.array", { n: (Array.isArray(value.shape) ? value.shape : []).join("×"), min: scalar(value.min ?? null, lang), max: scalar(value.max ?? null, lang) })}
      <span className="subtle"> · {first.map((v) => scalar(v, lang)).join("; ")} … {scalar(value.last ?? null, lang)}</span></span>;
  }
  if (value._kind === "list") {
    const items = Array.isArray(value.items) ? value.items : [];
    return <details className="signal-tree" open={depth < 1}><summary>{t("live.list", { n: Number(value.count ?? items.length), shown: items.length })}</summary>
      {items.map((v, i) => <div key={i} className="signal-tree__row"><span className="subtle mono">{i}</span><SignalTree value={v} lang={lang} depth={depth + 1} /></div>)}</details>;
  }
  const entries = Object.entries(value).filter(([k]) => k !== "_more");
  const body = entries.map(([k, v]) => <div key={k} className="signal-tree__row"><span className="mono signal-tree__key">{k}</span><SignalTree value={v} lang={lang} depth={depth + 1} /></div>);
  if (depth === 0) return <div className="signal-tree">{body}</div>;
  return <details className="signal-tree" open={entries.length <= 4 && entries.every(([, v]) => flat(v))}><summary>{t("live.fields", { n: entries.length })}</summary>{body}</details>;
}
