import i18n from "i18next";
import LanguageDetector from "i18next-browser-languagedetector";
import { initReactI18next } from "react-i18next";

import deApp from "./locales/de/app.json";
import deCommon from "./locales/de/common.json";
import deDomain from "./locales/de/domain.json";
import deInspector from "./locales/de/inspector.json";
import deLanding from "./locales/de/landing.json";
import enApp from "./locales/en/app.json";
import enCommon from "./locales/en/common.json";
import enDomain from "./locales/en/domain.json";
import enInspector from "./locales/en/inspector.json";
import enLanding from "./locales/en/landing.json";

export const LANGUAGES = [
  { code: "en", label: "English" },
  { code: "de", label: "Deutsch" },
] as const;
export const NAMESPACES = ["common", "app", "domain", "inspector", "landing"] as const;
export const LANGUAGE_STORAGE_KEY = "me.lang";

export const resources = {
  en: { common: enCommon, app: enApp, domain: enDomain, inspector: enInspector, landing: enLanding },
  de: { common: deCommon, app: deApp, domain: deDomain, inspector: deInspector, landing: deLanding },
} as const;

// Detection: a language the user picked in the header (localStorage) wins; without one the
// browser language is used; English is the fallback for every other language.
void i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    ns: [...NAMESPACES],
    defaultNS: "common",
    fallbackLng: "en",
    supportedLngs: LANGUAGES.map((l) => l.code),
    nonExplicitSupportedLngs: true,
    load: "languageOnly",
    interpolation: { escapeValue: false },
    detection: {
      order: ["localStorage", "navigator", "htmlTag"],
      lookupLocalStorage: LANGUAGE_STORAGE_KEY,
      caches: ["localStorage"],
    },
    returnNull: false,
  });

const setHtmlLang = (lng?: string) => {
  if (typeof document !== "undefined") document.documentElement.lang = (lng ?? "en").split("-")[0];
};
i18n.on("languageChanged", setHtmlLang);
i18n.on("initialized", () => setHtmlLang(i18n.resolvedLanguage));
setHtmlLang(i18n.resolvedLanguage);

export default i18n;
