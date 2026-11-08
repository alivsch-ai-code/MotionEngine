import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";

export type Theme = "dark" | "light";
export interface Settings {
  apiBase: string;   // "" = same origin as the web app
  apiKey: string;
  theme: Theme;
}

const KEY = "me.settings";
const read = (): Settings => {
  const theme = (document.documentElement.dataset.theme as Theme) || "dark";
  try {
    const s = JSON.parse(localStorage.getItem(KEY) ?? "{}") as Partial<Settings>;
    return { apiBase: s.apiBase ?? "", apiKey: s.apiKey ?? "", theme };
  } catch {
    return { apiBase: "", apiKey: "", theme };
  }
};

interface Ctx extends Settings {
  update: (patch: Partial<Settings>) => void;
}
const SettingsContext = createContext<Ctx | null>(null);

export function SettingsProvider({ children }: { children: ReactNode }) {
  const [settings, setSettings] = useState<Settings>(read);
  const update = useCallback((patch: Partial<Settings>) => {
    setSettings((prev) => {
      const next = { ...prev, ...patch };
      try {
        localStorage.setItem(KEY, JSON.stringify({ apiBase: next.apiBase, apiKey: next.apiKey }));
        localStorage.setItem("me.theme", next.theme);
      } catch {
        /* storage unavailable (private mode): settings live for this session only */
      }
      document.documentElement.dataset.theme = next.theme;
      return next;
    });
  }, []);
  const value = useMemo(() => ({ ...settings, update }), [settings, update]);
  return <SettingsContext.Provider value={value}>{children}</SettingsContext.Provider>;
}

export function useSettings(): Ctx {
  const ctx = useContext(SettingsContext);
  if (!ctx) throw new Error("useSettings outside SettingsProvider");
  return ctx;
}
