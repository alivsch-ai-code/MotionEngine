// LaTeX rendering with KaTeX; the KaTeX bundle (~270 kB) is loaded only on pages that show formulas.
import { memo, useEffect, useRef, useState } from "react";

type Katex = typeof import("katex").default;
let katexPromise: Promise<Katex> | null = null;
function loadKatex() {
  katexPromise ??= Promise.all([import("katex"), import("katex/dist/katex.min.css")]).then(([m]) => m.default);
  return katexPromise;
}

export const Formula = memo(function Formula({ tex, display = true }: { tex: string; display?: boolean }) {
  const ref = useRef<HTMLDivElement>(null);
  const [ready, setReady] = useState(false);
  useEffect(() => {
    let alive = true;
    void loadKatex().then((katex) => {
      if (!alive || !ref.current) return;
      katex.render(tex, ref.current, { displayMode: display, throwOnError: false, strict: "ignore", output: "htmlAndMathml" });
      setReady(true);
    });
    return () => { alive = false; };
  }, [tex, display]);
  // KaTeX owns the inner element (it replaces its content); React only manages the wrapper and the placeholder
  return (
    <div className="formula" aria-busy={!ready}>
      <div ref={ref} />
      {ready ? null : <code className="subtle">{tex}</code>}
    </div>
  );
});
