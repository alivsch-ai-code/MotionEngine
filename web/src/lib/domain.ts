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
