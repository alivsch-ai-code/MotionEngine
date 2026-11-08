// MotionEngine mark (docs/brand/motionengine-mark.svg) as a component: one gradient id per instance.
import { useId } from "react";

export function LogoMark({ size = 28, title }: { size?: number; title?: string }) {
  const id = useId();
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" role={title ? "img" : undefined} aria-hidden={title ? undefined : true}>
      {title ? <title>{title}</title> : null}
      <defs>
        <linearGradient id={id} x1="0" y1="1" x2="1" y2="0">
          <stop offset="0" stopColor="#2563EB" />
          <stop offset="1" stopColor="#06B6D4" />
        </linearGradient>
      </defs>
      <path d="M8 52 V22 C8 12 18 10 22 18 L27 28 L32 18 C36 10 46 12 46 22 V36 C46 46 50 50 56 50" fill="none"
        stroke={`url(#${id})`} strokeWidth="6" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M55 44 L63 50 L55 56 L57.5 50 Z" fill="#06B6D4" />
    </svg>
  );
}

export function Wordmark() {
  return (
    <span className="wordmark" style={{ fontWeight: 700, letterSpacing: "-0.01em" }}>
      Motion<span style={{ color: "var(--me-primary)" }}>Engine</span>
    </span>
  );
}
