// Translated labels of backend keys (parameters, KPIs, maneuvers, models); unknown keys fall back to the key.
import type { TFunction } from "i18next";

import type { Kpi } from "./api";

export const paramLabel = (t: TFunction, key: string) => t(`domain:param.${key}`, { defaultValue: key });
export const kpiLabel = (t: TFunction, k: Pick<Kpi, "key" | "label">) => t(`domain:kpi.${k.key}`, { defaultValue: k.label });
export const maneuverLabel = (t: TFunction, name: string) => t(`domain:maneuver.${name}.label`, { defaultValue: name });
export const maneuverDescription = (t: TFunction, name: string) => t(`domain:maneuver.${name}.description`, { defaultValue: "" });
export const maneuverParamLabel = (t: TFunction, name: string) => t(`domain:maneuverParam.${name}`, { defaultValue: name });
export const modelLabel = (t: TFunction, name: string) =>
  name.startsWith("neural_") ? t("app:models.neuralModel", { id: name.slice(7) }) : t(`app:vehicleModels.${name}`, { defaultValue: name });
export const controllerLabel = (t: TFunction, name: string) => t(`app:controllers.${name}`, { defaultValue: name });
export const kpiValue = (t: TFunction, k: Kpi) => (typeof k.value === "string" ? t(`app:kpiValues.${k.value_code ?? "other"}`, { defaultValue: k.value }) : k.value);

// Units are SI symbols and stay untranslated; only the KPI degree units are normalized.
export const unitLabel = (unit: string) => unit.replace("°/s", "°/s").replace("-", "");

export const adScenarioLabel = (t: TFunction, s: { name: string; label?: string }) => t(`domain:adScenarioLabel.${s.name}`, { defaultValue: s.label || s.name });
export const componentLabel = (t: TFunction, spec: string, fallback = "") => t(`domain:component.${spec.replace("/", ".")}`, { defaultValue: fallback || spec });

// Sentences the library builds at run time (mission criteria, graph validation, stop reasons) are German.
// For other languages the known patterns are translated here; an unknown sentence is shown unchanged.
const LIBRARY_PATTERNS: [RegExp, string][] = [
  [/^keine Kollision$/, "no collision"],
  [/^Kollision mit (.+)$/, "collision with $1"],
  [/^(\d+) Schritte neben der Fahrbahn$/, "$1 steps off the road"],
  [/^Spur (.+)$/, "lane $1"],
  [/^(\S+) m gefahren$/, "$1 m driven"],
  [/^Abstand zum Ziel (\S+) m$/, "distance to the goal $1 m"],
  [/^kein Ziel definiert$/, "no goal defined"],
  [/^s = (\S+) m auf (.+)$/, "s = $1 m on $2"],
  [/^Simulationsdauer erreicht$/, "simulation time reached"],
  [/^Ziel erreicht$/, "goal reached"],
  [/^Kollision$/, "collision"],
  [/^Rechenzeitlimit$/, "computing time limit"],
  [/^numerisch instabil.*$/, "numerically unstable"],
  [/^(?:Fehler: )?Pflichteingang (\S+) \((.+)\) ist nicht verbunden$/, "Error: required input $1 ($2) is not connected"],
  [/^(?:Fehler: )?Typkonflikt: (\S+) liefert '(.+)', (\S+) erwartet '(.+)'$/, "Error: type conflict: $1 provides '$2', $3 expects '$4'"],
  [/^(?:Fehler: )?Verbindung (\S+) → (\S+): Knoten '(.+)' existiert nicht$/, "Error: connection $1 → $2: node '$3' does not exist"],
  [/^(?:Fehler: )?Eingang (\S+) ist mehrfach belegt \(von (.+)\)$/, "Error: input $1 has several sources ($2)"],
  [/^Fehler: (.*)$/, "Error: $1"],
  [/^Warnung: (.*)$/, "Warning: $1"],
];
export function libraryText(text: string | null | undefined, lang: string): string {
  if (!text) return "";
  if (lang.startsWith("de")) return text;
  for (const [pattern, replacement] of LIBRARY_PATTERNS) if (pattern.test(text)) return text.replace(pattern, replacement);
  return text;
}
