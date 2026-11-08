import { useId, type ReactNode } from "react";

import { InfoTip } from "./Tooltip";

interface Base { label: ReactNode; hint?: ReactNode; tip?: ReactNode }

export function NumberField({ label, hint, tip, unit, value, onChange, min, max, step = "any" }:
  Base & { unit?: string; value: number; onChange: (v: number) => void; min?: number; max?: number; step?: number | "any" }) {
  const id = useId();
  return (
    <div className="field">
      <label className="field__label" htmlFor={id}>{label}{tip ? <InfoTip text={tip} /> : null}</label>
      <div className="field__control">
        <input id={id} className={`input${unit ? " input--unit" : ""}`} type="number" inputMode="decimal" value={Number.isFinite(value) ? value : ""}
          min={min} max={max} step={step} onChange={(e) => onChange(e.target.valueAsNumber)} />
        {unit ? <span className="field__unit">{unit}</span> : null}
      </div>
      {hint ? <span className="field__hint">{hint}</span> : null}
    </div>
  );
}

export function SelectField<T extends string>({ label, hint, tip, value, onChange, options }:
  Base & { value: T; onChange: (v: T) => void; options: { value: T; label: string }[] }) {
  const id = useId();
  return (
    <div className="field">
      <label className="field__label" htmlFor={id}>{label}{tip ? <InfoTip text={tip} /> : null}</label>
      <select id={id} className="select" value={value} onChange={(e) => onChange(e.target.value as T)}>
        {options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
      {hint ? <span className="field__hint">{hint}</span> : null}
    </div>
  );
}

export function TextField({ label, hint, tip, value, onChange, type = "text", placeholder }:
  Base & { value: string; onChange: (v: string) => void; type?: string; placeholder?: string }) {
  const id = useId();
  return (
    <div className="field">
      <label className="field__label" htmlFor={id}>{label}{tip ? <InfoTip text={tip} /> : null}</label>
      <input id={id} className="input" type={type} value={value} placeholder={placeholder} onChange={(e) => onChange(e.target.value)} />
      {hint ? <span className="field__hint">{hint}</span> : null}
    </div>
  );
}

export function CheckboxField({ label, checked, onChange }: { label: ReactNode; checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <label className="checkbox"><input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} />{label}</label>
  );
}
