// MATLAB: analyze MATLAB code and convert it to Python or C (vdsim.matlab).
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { EmptyState } from "../components/EmptyState";
import { ErrorAlert } from "../components/ErrorAlert";
import { Icon } from "../components/Icon";
import { PageHeader } from "../components/PageHeader";
import { useClient, useMutation, usePersistentState } from "../lib/hooks";

const SAMPLE = `function [delta, e] = stanley(psi_err, e_lat, v, k)
% Stanley lateral controller
  k_soft = 1.0;
  e = e_lat;
  delta = psi_err + atan(k * e_lat / (k_soft + v));
  delta = max(min(delta, 0.6), -0.6);
end
`;

export default function Matlab() {
  const { t } = useTranslation(["app", "common"]);
  const client = useClient();
  const [source, setSource] = usePersistentState("me.matlab.source", SAMPLE);
  const [target, setTarget] = useState<"python" | "c">("python");
  const run = useMutation(async (src: string, tgt: "python" | "c") => {
    const [analysis, code] = await Promise.all([client.matlabAnalyze(src), client.matlabConvert(src, tgt)]);
    return { analysis, code };
  });
  const out = run.data;
  return (
    <div className="stack stack--lg">
      <PageHeader title={t("matlab.title")} description={t("matlab.subtitle")} />
      <div className="grid grid--2">
        <form className="card" onSubmit={(e) => { e.preventDefault(); void run.run(source, target); }}>
          <div className="card__header"><h2>{t("matlab.source")}</h2>
            <div className="segmented" role="group" aria-label={t("matlab.target")}>
              {(["python", "c"] as const).map((x) => <button key={x} type="button" aria-pressed={target === x} onClick={() => setTarget(x)}>{t(`matlab.targets.${x}`)}</button>)}
            </div></div>
          <div className="card__body stack">
            <label htmlFor="matlab-src" className="visually-hidden">{t("matlab.source")}</label>
            <textarea id="matlab-src" className="input mono code-editor" spellCheck={false} rows={18} value={source} onChange={(e) => setSource(e.target.value)} />
            <div className="row">
              <button type="submit" className="btn btn--primary" disabled={run.loading || !source.trim()}>{run.loading ? <span className="spinner" /> : <Icon name="code" />}{t("matlab.convert")}</button>
              <button type="button" className="btn btn--ghost btn--sm" onClick={() => setSource(SAMPLE)}>{t("matlab.sample")}</button>
            </div>
          </div>
        </form>
        <div className="stack" aria-live="polite">
          <ErrorAlert error={run.error} />
          {!out && !run.error ? <div className="card"><EmptyState art="model" title={t("matlab.empty.title")} text={t("matlab.empty.text")} /></div> : null}
          {out ? Object.entries(out.code.files).map(([name, code]) => (
            <div key={name} className="card"><div className="card__header"><h2 className="mono">{name}</h2>
              <span className={`badge ${out.code.ok ? "badge--success" : "badge--warning"}`}>{out.code.ok ? t("matlab.ok") : t("matlab.warnings")}</span></div>
              <div className="card__body"><pre className="code-block code-block--scroll">{code}</pre></div></div>
          )) : null}
          {out?.analysis.functions.length ? (
            <div className="card"><div className="card__header"><h2>{t("matlab.analysis")}</h2></div><div className="card__body table-wrap"><table className="table">
              <thead><tr><th>{t("matlab.function")}</th><th>{t("matlab.variable")}</th><th>{t("matlab.role")}</th><th>{t("matlab.type")}</th></tr></thead>
              <tbody>{out.analysis.functions.flatMap((f) => Object.entries(f.variables).map(([name, v]) => (
                <tr key={`${f.name}.${name}`}><td className="mono">{f.name}</td><td className="mono">{name}</td><td>{v.role}</td><td className="subtle">{v.type}</td></tr>)))}</tbody>
            </table>
            {out.analysis.builtins?.length ? <p className="subtle">{t("matlab.builtins")}: <span className="mono">{out.analysis.builtins.join(", ")}</span></p> : null}
            {out.analysis.diagnostics?.length ? <pre className="code-block">{JSON.stringify(out.analysis.diagnostics, null, 1)}</pre> : null}
            </div></div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
