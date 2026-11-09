// Training jobs live on the server; this context follows the current job for the whole app, so leaving the
// Models page does not lose it: the header shows the progress everywhere and the page picks it up again.
import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

import type { TrainJob, TrainRequest } from "./api";
import { useClient } from "./hooks";

const ACTIVE = new Set(["queued", "running"]);
export const isActive = (job: TrainJob | null | undefined) => Boolean(job && ACTIVE.has(job.state));

interface TrainingCtx {
  job: TrainJob | null;
  starting: boolean;
  error: unknown;
  start: (body: TrainRequest) => Promise<TrainJob | undefined>;
  cancel: () => Promise<void>;
  dismiss: () => void;
}

const Ctx = createContext<TrainingCtx | null>(null);

export function TrainingProvider({ children }: { children: ReactNode }) {
  const client = useClient();
  const [job, setJob] = useState<TrainJob | null>(null);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<unknown>(null);

  // resume: the most recent job that is still running (e.g. after a reload or a page change)
  useEffect(() => {
    const ctrl = new AbortController();
    client.jobs(ctrl.signal).then((jobs) => {
      const active = jobs.find((j) => ACTIVE.has(j.state));
      if (active) setJob(active);
    }, () => undefined);
    return () => ctrl.abort();
  }, [client]);

  const id = job?.id;
  const active = isActive(job);
  useEffect(() => {
    if (!id || !active) return;
    const timer = window.setInterval(() => {
      client.job(id).then(setJob, () => undefined);
    }, 700);
    return () => window.clearInterval(timer);
  }, [id, active, client]);

  const start = useCallback(async (body: TrainRequest) => {
    setStarting(true);
    setError(null);
    try {
      const j = await client.train(body);
      setJob(j);
      return j;
    } catch (err) {
      setError(err);
      return undefined;
    } finally {
      setStarting(false);
    }
  }, [client]);

  const cancel = useCallback(async () => {
    if (id) setJob(await client.cancelJob(id));
  }, [client, id]);

  const dismiss = useCallback(() => { setJob(null); setError(null); }, []);
  const value = useMemo(() => ({ job, starting, error, start, cancel, dismiss }), [job, starting, error, start, cancel, dismiss]);
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useTraining(): TrainingCtx {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useTraining outside TrainingProvider");
  return ctx;
}
