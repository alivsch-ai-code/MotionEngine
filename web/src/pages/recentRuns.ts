// Last simulation runs of this browser session (shown on the dashboard).
export interface RecentRun { at: number; maneuver: string; model: string; maxAy: number | null; wall: number }
const KEY = "me.recentRuns";

export function readRecentRuns(): RecentRun[] {
  try {
    return JSON.parse(sessionStorage.getItem(KEY) ?? "[]") as RecentRun[];
  } catch {
    return [];
  }
}

export function addRecentRun(run: RecentRun) {
  try {
    sessionStorage.setItem(KEY, JSON.stringify([run, ...readRecentRuns()].slice(0, 8)));
  } catch {
    /* storage unavailable */
  }
}
