// Time-series chart on uPlot (canvas, ~50 kB): thousands of points without DOM nodes per point.
// The plot instance is created once per series layout and updated with setData; size follows the container.
import "uplot/dist/uPlot.min.css";

import { memo, useEffect, useRef } from "react";
import uPlot from "uplot";

export interface Series { label: string; values: (number | null)[]; color?: number; dash?: boolean }

const css = (name: string) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

function ChartImpl({ x, series, xLabel, yLabel, height = 240, ariaLabel }:
  { x: (number | null)[]; series: Series[]; xLabel: string; yLabel: string; height?: number; ariaLabel: string }) {
  const host = useRef<HTMLDivElement>(null);
  const plot = useRef<uPlot | null>(null);
  const layout = series.map((s) => `${s.label}|${s.color ?? ""}|${s.dash ? 1 : 0}`).join(";") + `|${xLabel}|${yLabel}|${height}`;
  const theme = typeof document !== "undefined" ? document.documentElement.dataset.theme : "dark";

  useEffect(() => {
    const el = host.current;
    if (!el) return;
    const axis = { stroke: css("--me-chart-axis"), grid: { stroke: css("--me-chart-grid"), width: 1 }, ticks: { stroke: css("--me-chart-grid") },
      font: `12px ${css("--me-font-sans")}`, labelFont: `12px ${css("--me-font-sans")}` };
    const opts: uPlot.Options = {
      width: Math.max(el.clientWidth, 200), height,
      cursor: { drag: { x: true, y: false } },
      legend: { show: series.length > 1 },
      scales: { x: { time: false } },
      axes: [{ ...axis, label: xLabel }, { ...axis, label: yLabel, size: 56 }],
      series: [{ label: xLabel }, ...series.map((s, i) => ({
        label: s.label, stroke: css(`--me-chart-${(s.color ?? i) % 6 + 1}`), width: 2, dash: s.dash ? [6, 4] : undefined, spanGaps: false,
        points: { show: false },
      }))],
    };
    const p = new uPlot(opts, [x as number[], ...series.map((s) => s.values as number[])], el);
    plot.current = p;
    const ro = new ResizeObserver(() => p.setSize({ width: Math.max(el.clientWidth, 200), height }));
    ro.observe(el);
    return () => { ro.disconnect(); p.destroy(); plot.current = null; };
    // re-create only when the layout or theme changes; data updates go through setData below
  }, [layout, theme]); // eslint-disable-line

  useEffect(() => {
    plot.current?.setData([x as number[], ...series.map((s) => s.values as number[])]);
  }, [x, series]);

  return <div className="chart" ref={host} role="img" aria-label={ariaLabel} />;
}

export const Chart = memo(ChartImpl);
export default Chart;
