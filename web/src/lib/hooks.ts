import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { createClient, type Client } from "./api";
import { useSettings } from "./settings";

export function useClient(): Client {
  const { apiBase, apiKey } = useSettings();
  return useMemo(() => createClient({ apiBase, apiKey }), [apiBase, apiKey]);
}

export interface AsyncState<T> { data: T | undefined; error: unknown; loading: boolean; reload: () => void }

// Loads data on mount and whenever `deps` change; aborts the request on unmount (no setState after unmount).
export function useQuery<T>(fn: (signal: AbortSignal) => Promise<T>, deps: unknown[]): AsyncState<T> {
  const [state, setState] = useState<{ data?: T; error?: unknown; loading: boolean }>({ loading: true });
  const [tick, setTick] = useState(0);
  const fnRef = useRef(fn);
  fnRef.current = fn;
  useEffect(() => {
    const ctrl = new AbortController();
    setState((s) => ({ data: s.data, loading: true }));
    fnRef.current(ctrl.signal).then(
      (data) => !ctrl.signal.aborted && setState({ data, loading: false }),
      (error) => !ctrl.signal.aborted && setState({ error, loading: false }),
    );
    return () => ctrl.abort();
  }, [...deps, tick]);
  const reload = useCallback(() => setTick((n) => n + 1), []);
  return { data: state.data, error: state.error, loading: state.loading, reload };
}

// Runs an action on demand (form submit); keeps the last result.
export function useMutation<A extends unknown[], T>(fn: (...args: A) => Promise<T>) {
  const [state, setState] = useState<{ data?: T; error?: unknown; loading: boolean }>({ loading: false });
  const run = useCallback(async (...args: A) => {
    setState((s) => ({ data: s.data, loading: true }));
    try {
      const data = await fn(...args);
      setState({ data, loading: false });
      return data;
    } catch (error) {
      setState({ error, loading: false });
      return undefined;
    }
  }, [fn]);
  return { ...state, run, reset: () => setState({ loading: false }) };
}

export function usePersistentState<T>(key: string, initial: T): [T, (v: T) => void] {
  const [value, setValue] = useState<T>(() => {
    try {
      const raw = sessionStorage.getItem(key);
      return raw ? (JSON.parse(raw) as T) : initial;
    } catch {
      return initial;
    }
  });
  const set = useCallback((v: T) => {
    setValue(v);
    try {
      sessionStorage.setItem(key, JSON.stringify(v));
    } catch {
      /* ignore */
    }
  }, [key]);
  return [value, set];
}
