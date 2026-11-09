// Animated top view of a parking result: spot, parked vehicles, curbs, the planned moves (forward solid,
// reverse dashed) and the vehicle driving them. Used by the Parking page and the assistant.
import { memo, useMemo } from "react";

import type { ParkResponse } from "../lib/api";
import type { Polyline } from "./PathPlot";
import { TrackPlayer, type Area, type Track } from "./TrackPlayer";

function ParkingViewImpl({ r, height = 360, autoPlay = true, ariaLabel }: { r: ParkResponse; height?: number; autoPlay?: boolean; ariaLabel: string }) {
  const areas = useMemo<Area[]>(() => [
    { points: r.scenario.spot as [number, number][], kind: "spot" },
    ...r.scenario.obstacles.map((o) => ({ points: o.polygon as [number, number][], kind: o.kind as Area["kind"] })),
  ], [r]);
  const lines = useMemo<Polyline[]>(() => {
    if (!r.path) return [];
    const out: Polyline[] = [];
    const d = r.path.direction;
    let start = 0;
    for (let i = 1; i <= d.length; i++) {
      if (i === d.length || d[i] !== d[start]) {
        const a = Math.max(start - 1, 0);
        out.push({ x: r.path.x.slice(a, i), y: r.path.y.slice(a, i), kind: d[start] > 0 ? "selected" : "prediction" });
        start = i;
      }
    }
    return out;
  }, [r]);
  const track = useMemo<Track>(() => (r.driven
    ? { t: r.driven.t, x: r.driven.x, y: r.driven.y, psi: r.driven.psi, v: r.driven.v, length: r.footprint.length, width: r.footprint.width }
    : { t: [0], x: [r.scenario.start[0]], y: [r.scenario.start[1]], psi: [r.scenario.start[2]], length: r.footprint.length, width: r.footprint.width }), [r]);
  return <TrackPlayer track={track} areas={areas} lines={lines} height={height} follow={false} followWidth={25}
    autoPlay={autoPlay && Boolean(r.driven)} ariaLabel={ariaLabel} />;
}

export const ParkingView = memo(ParkingViewImpl);
