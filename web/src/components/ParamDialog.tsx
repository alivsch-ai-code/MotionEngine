// Parameter dialog of a stack component: one field per parameter, built from the component's schema
// (name, default, unit, label, choices, limits). Returns only the values that differ from the defaults.
// (Desktop equivalent: ParamDialog with the parameter tree.)
import { useEffect, useId, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { useTranslation } from "react-i18next";

import type { ComponentParam } from "../lib/api";
import { Icon } from "./Icon";

type Obj = Record<string, unknown>;
const isObj = (v: unknown): v is Obj => typeof v === "object" && v !== null && !Array.isArray(v);
const same = (a: unknown, b: unknown) => JSON.stringify(a) === JSON.stringify(b);

// defaults with the overrides applied (deep)
export function mergeParams(defaults: Obj, overrides: Obj): Obj {
  const out: Obj = { ...defaults };
  for (const [k, v] of Object.entries(overrides)) out[k] = isObj(v) && isObj(defaults[k]) ? mergeParams(defaults[k] as Obj, v) : v;
  return out;
}

// the values that differ from the defaults (deep); empty object when nothing changed
export function changedParams(defaults: Obj, values: Obj): Obj {
  const out: Obj = {};
  for (const [k, v] of Object.entries(values)) {
    const d = defaults[k];
    if (isObj(v) && isObj(d)) {
      const sub = changedParams(d, v);
      if (Object.keys(sub).length) out[k] = sub;
    } else if (!same(v, d)) out[k] = v;
  }
  return out;
}

function parseList(text: string, def: unknown[]): unknown[] {
  const parts = text.split(/[,;]/).map((p) => p.trim()).filter(Boolean);
  if (def.every((d) => typeof d === "number")) return parts.map(Number).filter((n) => Number.isFinite(n));
  return parts;
}

function Leaf({ entry, def, value, onChange }: { entry: Partial<ComponentParam> & { name: string }; def: unknown; value: unknown; onChange: (v: unknown) => void }) {
  const id = useId();
  const label = entry.label || entry.name;
  const changed = !same(value, def);
  const unit = entry.unit && entry.unit !== "-" ? entry.unit : "";
  let control;
  if (entry.choices?.length) {
    control = <select id={id} className="select" value={String(value)} onChange={(e) => onChange(typeof def === "number" ? Number(e.target.value) : e.target.value)}>
      {entry.choices.map((c) => <option key={String(c)} value={String(c)}>{String(c)}</option>)}</select>;
  } else if (typeof def === "boolean") {
    control = <input id={id} type="checkbox" checked={Boolean(value)} onChange={(e) => onChange(e.target.checked)} />;
  } else if (typeof def === "number") {
    control = <input id={id} className="input" type="number" inputMode="decimal" step={entry.step ?? "any"} min={entry.min} max={entry.max}
      value={typeof value === "number" && Number.isFinite(value) ? value : ""} onChange={(e) => onChange(Number.isFinite(e.target.valueAsNumber) ? e.target.valueAsNumber : def)} />;
  } else if (Array.isArray(def)) {
    control = <input id={id} className="input mono" type="text" defaultValue={(Array.isArray(value) ? value : def).join(", ")} key={JSON.stringify(value)}
      onBlur={(e) => onChange(parseList(e.target.value, def))} />;
  } else {
    control = <input id={id} className="input" type="text" value={value === null || value === undefined ? "" : String(value)}
      onChange={(e) => onChange(e.target.value === "" && def === null ? null : e.target.value)} />;
  }
  return (
    <div className={`param-row${changed ? " param-row--changed" : ""}`}>
      <label htmlFor={id} title={entry.description || undefined}>{label}{unit ? <span className="subtle"> [{unit}]</span> : null}</label>
      {control}
    </div>
  );
}

function Group({ entry, def, value, onChange, depth }: { entry: Partial<ComponentParam> & { name: string }; def: Obj; value: Obj; onChange: (v: Obj) => void; depth: number }) {
  const n = Object.keys(changedParams(def, value)).length;
  return (
    <details className="param-group" open={depth === 0 && Object.keys(def).length <= 8}>
      <summary>{entry.label || entry.name}{n ? <span className="badge badge--info">{n}</span> : null}</summary>
      {Object.entries(def).map(([k, d]) => (isObj(d)
        ? <Group key={k} entry={{ name: k }} def={d} value={isObj(value[k]) ? (value[k] as Obj) : d} depth={depth + 1} onChange={(v) => onChange({ ...value, [k]: v })} />
        : <Leaf key={k} entry={{ name: k }} def={d} value={value[k]} onChange={(v) => onChange({ ...value, [k]: v })} />))}
    </details>
  );
}

export function ParamDialog({ title, schema, overrides, onApply, onClose }:
  { title: string; schema: ComponentParam[]; overrides: Obj; onApply: (changed: Obj) => void; onClose: () => void }) {
  const { t } = useTranslation(["app", "common"]);
  const ref = useRef<HTMLDialogElement>(null);
  const defaults = Object.fromEntries(schema.map((p) => [p.name, p.default])) as Obj;
  const [values, setValues] = useState<Obj>(() => mergeParams(defaults, overrides));
  useEffect(() => {
    const el = ref.current;
    if (el && !el.open) el.showModal();
  }, []);
  const changed = changedParams(defaults, values);
  const n = Object.keys(changed).length;
  // rendered at the document root and without a form of its own: the editor sits inside the page's run form
  return createPortal(
    <dialog ref={ref} className="dialog" onClose={onClose} aria-labelledby="param-dialog-title" onSubmit={(e) => e.stopPropagation()} onClick={(e) => e.stopPropagation()}>
      <div className="dialog__body">
        <div className="row row--between">
          <h2 id="param-dialog-title">{t("params.title", { name: title })}</h2>
          <button type="button" className="btn btn--ghost btn--sm btn--icon" aria-label={t("common:close")} onClick={onClose}><Icon name="x" size={16} /></button>
        </div>
        <p className="subtle">{t("params.text")}</p>
        <div className="dialog__scroll">
          {schema.map((p) => (isObj(p.default)
            ? <Group key={p.name} entry={p} def={p.default} value={isObj(values[p.name]) ? (values[p.name] as Obj) : p.default} depth={0}
              onChange={(v) => setValues({ ...values, [p.name]: v })} />
            : <Leaf key={p.name} entry={p} def={p.default} value={values[p.name]} onChange={(v) => setValues({ ...values, [p.name]: v })} />))}
        </div>
        <div className="row row--between">
          <button type="button" className="btn btn--ghost btn--sm" disabled={!n} onClick={() => setValues(defaults)}>{t("params.defaults")}</button>
          <div className="row">
            <span className="subtle">{t("params.changed", { n })}</span>
            <button type="button" className="btn btn--secondary" onClick={onClose}>{t("common:cancel")}</button>
            <button type="button" className="btn btn--primary" onClick={() => onApply(changed)}>{t("params.apply")}</button>
          </div>
        </div>
      </div>
    </dialog>,
    document.body,
  );
}
