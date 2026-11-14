// Component per stack layer. Parameters are edited in a dialog built from the component schema; the
// overrides are kept as JSON and can also be edited as text.
import { useState } from "react";
import { useTranslation } from "react-i18next";

import type { WorkbenchCatalog } from "../lib/api";
import type { StackEdit } from "../lib/stack";
import { Icon } from "./Icon";
import { ParamDialog } from "./ParamDialog";

export function StackEditor({ catalog, stack, onChange }: { catalog: WorkbenchCatalog; stack: StackEdit; onChange: (s: StackEdit) => void }) {
  const { t } = useTranslation(["app", "common", "domain"]);
  const changed = Object.keys(stack).length;
  const [dialog, setDialog] = useState<string | null>(null);
  return (
    <details className="expert">
      <summary><Icon name="layers" />{t("workbench.stack.title")}{changed ? ` (${t("workbench.stack.changed", { n: changed })})` : ""}</summary>
      <div className="stack">
        <p className="subtle">{t("workbench.stack.text")}</p>
        {catalog.layers.map((l) => {
          const edit = stack[l.layer];
          const spec = edit?.component ?? l.default ?? "";
          const comp = l.components.find((c) => c.spec === spec);
          const set = (patch: Partial<{ component: string; paramsText: string }>) => {
            const next = { component: spec, paramsText: edit?.paramsText ?? "", ...patch };
            const rest = { ...stack };
            if (next.component === l.default && !next.paramsText.trim()) delete rest[l.layer]; else rest[l.layer] = next;
            onChange(rest);
          };
          const id = `stack-${l.layer}`;
          return (
            <div key={l.layer} className="field">
              <label className="field__label" htmlFor={id}>{t(`workbench.layers.${l.layer}`)}</label>
              <select id={id} className="select" value={spec} onChange={(e) => set({ component: e.target.value, paramsText: "" })}>
                {l.components.map((c) => <option key={c.spec} value={c.spec}>{c.spec.split("/")[1]}{c.spec === l.default ? ` (${t("workbench.stack.default")})` : ""}</option>)}
              </select>
              {comp ? <span className="field__hint">{t(`domain:component.${comp.spec.replace("/", ".")}`, { defaultValue: comp.label })}</span> : null}
              {comp?.params.length ? (
                <button type="button" className="btn btn--ghost btn--sm stack-params__edit" onClick={() => setDialog(l.layer)}>
                  <Icon name="settings" size={14} />{t("workbench.stack.edit", { n: comp.params.length })}{edit?.paramsText.trim() ? ` · ${t("workbench.stack.overridden")}` : ""}</button>
              ) : null}
              {dialog === l.layer && comp ? (
                <ParamDialog title={comp.spec} schema={comp.params} overrides={parseOverrides(edit?.paramsText ?? "")} onClose={() => setDialog(null)}
                  onApply={(c) => { set({ paramsText: Object.keys(c).length ? JSON.stringify(c, null, 1) : "" }); setDialog(null); }} />
              ) : null}
              {comp?.params.length ? (
                <details className="stack-params">
                  <summary>{t("workbench.stack.asJson")}</summary>
                  <textarea className="input mono stack-params__input" rows={3} spellCheck={false} value={edit?.paramsText ?? ""} aria-label={t("workbench.stack.overrides")}
                    placeholder={t("workbench.stack.placeholder")} onChange={(e) => set({ paramsText: e.target.value })} />
                  <pre className="mono stack-params__defaults">{JSON.stringify(Object.fromEntries(comp.params.map((p) => [p.name, p.default])), null, 1)}</pre>
                </details>
              ) : null}
            </div>
          );
        })}
        {changed ? <button type="button" className="btn btn--ghost btn--sm" onClick={() => onChange({})}>{t("common:reset")}</button> : null}
      </div>
    </details>
  );
}

function parseOverrides(text: string): Record<string, unknown> {
  try {
    const v: unknown = text.trim() ? JSON.parse(text) : {};
    return typeof v === "object" && v !== null && !Array.isArray(v) ? (v as Record<string, unknown>) : {};
  } catch {
    return {};
  }
}
