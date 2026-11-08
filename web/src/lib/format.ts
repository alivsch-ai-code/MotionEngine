// Locale-aware number formatting with engineering precision.
export function fmt(value: number | null | undefined, lang: string, digits = 3): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return "–";
  const abs = Math.abs(value);
  if (abs !== 0 && (abs >= 1e6 || abs < 1e-3)) return value.toExponential(digits - 1).replace("e", " · 10^");
  const maxFrac = abs >= 100 ? 1 : abs >= 10 ? 2 : digits;
  return new Intl.NumberFormat(lang, { maximumFractionDigits: maxFrac, minimumFractionDigits: 0 }).format(value);
}

export const toDeg = (rad: number) => (rad * 180) / Math.PI;
