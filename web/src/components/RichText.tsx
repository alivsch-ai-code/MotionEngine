// Minimal Markdown: headings, paragraphs, bullet and numbered lists, **bold** and `code`.
// Rendered as React elements, never as HTML.
import { Fragment, memo, useMemo, type ReactNode } from "react";

function inline(text: string): ReactNode[] {
  return text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g).map((s, i) => {
    if (s.startsWith("**") && s.endsWith("**") && s.length > 4) return <strong key={i}>{s.slice(2, -2)}</strong>;
    if (s.startsWith("`") && s.endsWith("`") && s.length > 2) return <code key={i} className="mono">{s.slice(1, -1)}</code>;
    return <Fragment key={i}>{s.replace(/\*([^*]+)\*/g, "$1")}</Fragment>;
  });
}

export const RichText = memo(function RichText({ text, headings = false }: { text: string; headings?: boolean }) {
  const blocks = useMemo(() => {
    const out: { kind: "p" | "ul" | "ol" | "h"; lines: string[] }[] = [];
    for (const raw of text.split("\n")) {
      const line = raw.trimEnd();
      const bullet = /^\s*[-*•]\s+(.*)$/.exec(line);
      const numbered = /^\s*\d+[.)]\s+(.*)$/.exec(line);
      const heading = /^#+\s+(.*)$/.exec(line);
      const kind = heading ? "h" : bullet ? "ul" : numbered ? "ol" : "p";
      const content = heading?.[1] ?? bullet?.[1] ?? numbered?.[1] ?? line;
      if (!line.trim()) { out.push({ kind: "p", lines: [] }); continue; }
      const last = out[out.length - 1];
      if (kind !== "h" && last && last.kind === kind && (kind !== "p" || last.lines.length)) last.lines.push(content);
      else out.push({ kind, lines: [content] });
    }
    return out.filter((b) => b.lines.length);
  }, [text]);
  return (
    <div className="chat__text">
      {blocks.map((b, i) => b.kind === "h" ? (headings ? <h3 key={i}>{inline(b.lines[0])}</h3> : <p key={i}><strong>{inline(b.lines[0])}</strong></p>)
        : b.kind === "p" ? <p key={i}>{b.lines.map((l, j) => <Fragment key={j}>{j ? <br /> : null}{inline(l)}</Fragment>)}</p>
          : b.kind === "ul" ? <ul key={i}>{b.lines.map((l, j) => <li key={j}>{inline(l)}</li>)}</ul>
            : <ol key={i}>{b.lines.map((l, j) => <li key={j}>{inline(l)}</li>)}</ol>)}
    </div>
  );
});
