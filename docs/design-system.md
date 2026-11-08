# MotionEngine Design System

Single source of truth for the look and behavior of the MotionEngine web application (`web/`).
Tokens live in [`web/src/design/tokens.css`](../web/src/design/tokens.css), components in
[`web/src/design/components.css`](../web/src/design/components.css) and `web/src/components/`.
A live style guide is part of the app at **/app/design**.

## 1. Principles

1. **Engineers first.** Every number has a unit, every formula shows the values that went into it, and
   every result can be traced back to its source (paper section, equation, parameter).
2. **Defaults that work.** Each workflow runs with one click. Advanced options sit behind
   "Expert settings" (`details.expert`) and never block the basic path.
3. **Quiet surfaces, loud data.** Neutral slate surfaces, one blue for actions, cyan for highlights;
   color in charts carries meaning, never decoration.
4. **No dead ends.** Every page has an empty state with an illustration, an explanation and a call to
   action; every error says what failed and what to check.
5. **Accessible by default.** WCAG 2.1 AA contrast in both themes, keyboard focus ring on every control,
   landmarks, `aria-live` for results, `prefers-reduced-motion` honored.

## 2. Brand

| Asset | File | Use |
|---|---|---|
| Mark | `docs/brand/motionengine-mark.svg` | the "M" that turns into a planned trajectory and ends in a vehicle arrow |
| Logo, light backgrounds | `docs/brand/motionengine-logo-light.svg` | documents, slides, README on white |
| Logo, dark backgrounds | `docs/brand/motionengine-logo-dark.svg` | app header (dark), dark slides |
| App icon / favicon | `app-icon.svg`, `favicon.svg`, `favicon-16/32.png`, `apple-touch-icon.png`, `icon-192/512.png` | browsers, PWA manifest |
| GitHub avatar | `github-avatar.png` (500 × 500) | organization and repository avatar |
| Alternatives | `logo-option-a.svg` (trajectory symbol), `logo-option-c.svg` (vehicle with sensor field) | not used; kept for reference |

Clear space around the mark: one quarter of its height. Minimum size: 16 px (favicon). The gradient runs
from Primary `#2563EB` to Accent `#06B6D4`; on monochrome media use `#0F172A` or white.

## 3. Color

| Token | Dark | Light | Use |
|---|---|---|---|
| `--me-brand-primary` | `#2563EB` | `#2563EB` | brand blue |
| `--me-brand-secondary` | `#0F172A` | `#0F172A` | brand navy, app icon background |
| `--me-brand-accent` | `#06B6D4` | `#06B6D4` | brand cyan |
| `--me-bg` | `#0B1120` | `#F1F5F9` | page background |
| `--me-surface` / `-2` / `-3` | `#0F172A` / `#131D33` / `#1A2540` | `#FFFFFF` / `#F8FAFC` / `#EEF2F7` | cards, inputs, hover |
| `--me-border` / `-strong` | `#1E293B` / `#334155` | `#E2E8F0` / `#CBD5E1` | dividers, input borders |
| `--me-text` / `-strong` / `-muted` / `-subtle` | `#E2E8F0` / `#F8FAFC` / `#94A3B8` / `#64748B` | `#1E293B` / `#0F172A` / `#475569` / `#64748B` | text hierarchy |
| `--me-primary` | `#3B82F6` | `#2563EB` | links, focus, selected state (lifted on dark for contrast) |
| `--me-success` / `-warning` / `-danger` | `#22C55E` / `#F59E0B` / `#EF4444` | `#16A34A` / `#B45309` / `#DC2626` | status |
| `--me-chart-1 … 6` | blue, cyan, amber, violet, pink, green | darker variants | categorical series in fixed order |

Rules: one primary button per view; status colors only for status; series colors are assigned in the
order 1 → 6 and stay with their meaning across charts of one page (e.g. physics = 1, neural = 3).

## 4. Typography

System font stack (`Inter`, Segoe UI, Roboto, …) and a monospace stack for numbers in tables and code.
No web font is downloaded on the critical path. Numbers use tabular figures.

| Token | Size | Use |
|---|---|---|
| `--me-text-4xl` | 48 px | landing hero |
| `--me-text-3xl` | 32 px | landing section titles |
| `--me-text-2xl` | 24 px | KPI values |
| `--me-text-xl` | 20 px | page titles (`h1`) |
| `--me-text-lg` | 16 px | card titles (`h2`) |
| `--me-text-md` | 14 px | body |
| `--me-text-sm` | 13 px | tables, hints |
| `--me-text-xs` | 12 px | captions, axis labels, badges |

Weights: 400 body, 500 labels and buttons, 600 headings, 700 brand and hero.

## 5. Spacing, radius, motion

4 px grid: `--me-space-1 … 8` = 4, 8, 12, 16, 24, 32, 48, 64 px. Card padding 16 px, gap between cards
16 px, between page sections 24 px. Radius: 6 px controls, 10 px cards, 14 px app icon and hero art.
Transitions 120–200 ms with `cubic-bezier(0.2, 0, 0, 1)`, disabled for `prefers-reduced-motion`.

## 6. Components

| Component | Class / file | Notes |
|---|---|---|
| Button | `.btn` + `--primary`, `--secondary`, `--ghost`, `--danger`, sizes `--sm`, `--lg`, `--icon` | 36 px default height, icon left of the label, spinner while busy |
| Card | `.card`, `.card__header`, `.card__body`, `.card--interactive` | interactive cards highlight the border on hover |
| KPI tile | `KpiTile` | label, value with unit, optional warning badge |
| Field | `NumberField`, `SelectField`, `TextField`, `CheckboxField` | label, unit inside the input, hint below, info tooltip |
| Expert settings | `details.expert` | collapsed by default |
| Tabs, segmented control | `.tabs`, `.segmented` | `role="tab"` / `aria-pressed` |
| Table | `.table`, `.num` | right-aligned numbers, row hover |
| Badge, alert | `.badge--success/warning/danger/info`, `.alert--danger/info` | |
| Tooltip | `InfoTip` | hover and keyboard focus, text is the accessible description |
| Empty state | `EmptyState` with art `simulation`, `results`, `api`, `scenario`, `model` | illustration + title + text + action |
| Loading | `Skeleton`, `PageSkeleton`, `.spinner`, `.progress` | skeletons keep the layout stable |
| Chart | `Chart` (uPlot, canvas) | lazy-loaded, theme-aware, resizes with its container |
| Top view | `PathPlot` (SVG) | equal axis scale for world coordinates, `stretch` for Frenet plots |
| Formula | `Formula` (KaTeX) | lazy-loaded, LaTeX from the API |
| Stepper | `.steps`, `.step-link` | used by the trajectory inspector |

## 7. Charts

- Canvas (uPlot) for time series: thousands of points without one DOM node per point.
- Axis labels carry the unit in brackets (`t [s]`), the legend only appears for more than one series.
- Grid and axis colors come from `--me-chart-grid` / `--me-chart-axis`; charts are re-created on theme change.
- Top views use SVG with `vector-effect: non-scaling-stroke`, so line widths stay constant when zooming.

## 8. Writing and internationalization

- English is the default language, German the second one; every visible string is a translation key in
  `web/src/locales/{en,de}/*.json` (`common`, `app`, `inspector`, `landing`, `domain`).
- `domain.json` (parameters, KPIs, maneuvers) is generated from the library labels by
  `web/scripts/generate_domain_locales.py`; do not edit it by hand.
- Language detection: the user's choice in the header (stored in `localStorage`) → browser language →
  English.
- `web/src/__tests__/i18n.test.ts` fails on hardcoded JSX text, untranslated `aria-label`/`title`/`alt`,
  missing keys, keys present in only one language and mismatched interpolation variables.
- Units are SI symbols and are not translated; numbers are formatted with `Intl.NumberFormat` in the
  active language (decimal comma in German).
- Tone: short, active, concrete. Buttons are verbs ("Run simulation"), empty states say what to do next.
