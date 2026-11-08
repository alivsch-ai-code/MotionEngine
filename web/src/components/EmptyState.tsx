import type { ReactNode } from "react";

// Illustrations are drawn from the design tokens, so they follow the theme.
const ART: Record<string, ReactNode> = {
  simulation: (
    <>
      <rect x="10" y="18" width="140" height="80" rx="10" fill="var(--me-surface-2)" stroke="var(--me-border-strong)" />
      <path d="M22 84 C52 84 58 40 88 40 S124 64 140 30" fill="none" stroke="var(--me-primary)" strokeWidth="3" strokeLinecap="round" strokeDasharray="5 6" />
      <circle cx="22" cy="84" r="5" fill="var(--me-accent)" />
      <path d="M134 24 l10 4 -8 7z" fill="var(--me-primary)" />
    </>
  ),
  results: (
    <>
      <rect x="10" y="14" width="140" height="86" rx="10" fill="var(--me-surface-2)" stroke="var(--me-border-strong)" />
      {[30, 52, 74, 96, 118].map((x, i) => <rect key={x} x={x} y={88 - [20, 34, 26, 48, 14][i]} width="14" height={[20, 34, 26, 48, 14][i]} rx="3" fill="var(--me-border-strong)" />)}
      <path d="M24 88 H140" stroke="var(--me-text-subtle)" />
    </>
  ),
  api: (
    <>
      <rect x="14" y="36" width="52" height="44" rx="8" fill="var(--me-surface-2)" stroke="var(--me-border-strong)" />
      <rect x="94" y="36" width="52" height="44" rx="8" fill="var(--me-surface-2)" stroke="var(--me-border-strong)" />
      <path d="M66 58 H78 M82 58 H94" stroke="var(--me-danger)" strokeWidth="3" strokeLinecap="round" />
      <path d="M76 52 l8 12 M84 52 l-8 12" stroke="var(--me-danger)" strokeWidth="2.5" strokeLinecap="round" />
    </>
  ),
  scenario: (
    <>
      <path d="M10 96 L60 20 H100 L150 96 Z" fill="var(--me-surface-2)" stroke="var(--me-border-strong)" />
      <path d="M80 26 V40 M80 50 V64 M80 74 V90" stroke="var(--me-text-subtle)" strokeWidth="3" strokeLinecap="round" />
      <rect x="92" y="70" width="16" height="24" rx="4" fill="var(--me-primary)" />
    </>
  ),
  chat: (
    <>
      <rect x="12" y="16" width="96" height="54" rx="12" fill="var(--me-surface-2)" stroke="var(--me-border-strong)" />
      <path d="M30 70 L26 86 L46 70" fill="var(--me-surface-2)" stroke="var(--me-border-strong)" strokeLinejoin="round" />
      <path d="M28 36 H90 M28 50 H70" stroke="var(--me-text-subtle)" strokeWidth="3" strokeLinecap="round" />
      <rect x="64" y="58" width="84" height="40" rx="10" fill="var(--me-primary)" fillOpacity="0.18" stroke="var(--me-primary)" />
      <path d="M76 86 C92 86 96 70 110 70 S130 78 138 66" fill="none" stroke="var(--me-primary)" strokeWidth="3" strokeLinecap="round" />
    </>
  ),
  model: (
    <>
      {[[30, 34], [30, 58], [30, 82], [80, 46], [80, 70], [130, 58]].map(([x, y], i) => <circle key={i} cx={x} cy={y} r="9" fill="var(--me-surface-2)" stroke="var(--me-border-strong)" strokeWidth="2" />)}
      <g stroke="var(--me-primary)" strokeOpacity="0.55">
        {[34, 58, 82].flatMap((y1) => [46, 70].map((y2) => <path key={`${y1}-${y2}`} d={`M39 ${y1} L71 ${y2}`} />))}
        <path d="M89 46 L121 58 M89 70 L121 58" />
      </g>
    </>
  ),
};

export function EmptyState({ art, title, text, action }: { art: keyof typeof ART; title: ReactNode; text: ReactNode; action?: ReactNode }) {
  return (
    <div className="empty" role="status">
      <svg className="empty__art" viewBox="0 0 160 112" aria-hidden="true">{ART[art]}</svg>
      <h3>{title}</h3>
      <p>{text}</p>
      {action}
    </div>
  );
}

export function Skeleton({ height = 16, width = "100%" }: { height?: number; width?: number | string }) {
  return <div className="skeleton" style={{ height, width }} aria-hidden="true" />;
}
