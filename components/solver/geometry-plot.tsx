"use client";

import { useEffect, useRef, useState } from "react";
import Plotly from "plotly.js/lib/core";
import scatter from "plotly.js/lib/scatter";
import scatter3d from "plotly.js/lib/scatter3d";
import mesh3d from "plotly.js/lib/mesh3d";
import type { Data, Layout } from "plotly.js";
import type { Geometry } from "../../lib/geometry/derive";

Plotly.register([scatter, scatter3d, mesh3d]);

export default function GeometryPlot({ geometry }: { geometry: Geometry }) {
  const host = useRef<HTMLDivElement>(null);
  const [failure, setFailure] = useState(false);
  const [ready, setReady] = useState(false);
  useEffect(() => {
    const container = host.current!;
    // Each effect owns its own node: a late Plotly promise from a Strict Mode
    // remount must never purge a newer plot in the same React host.
    const element = document.createElement("div");
    container.append(element);
    let canceled = false;
    const { dimension, bound } = geometry;
    const data: Data[] = geometry.shapes.map(shape => {
      const coordinates = [0, 1, 2].map(axis => shape.points.map(p => p.some(v => Math.abs(v) > bound) ? null : p[axis] ?? 0));
      const common = { name: shape.name, x: coordinates[0], y: coordinates[1], showlegend: true };
      if (shape.kind === "plane" && shape.points.length >= 3) return { ...common, type: "mesh3d", z: coordinates[2], color: shape.color, opacity: 0.4, i: shape.points.slice(2).map(() => 0), j: shape.points.slice(2).map((_, i) => i + 1), k: shape.points.slice(2).map((_, i) => i + 2) };
      return { ...common, type: dimension === 2 ? "scatter" : "scatter3d", ...(dimension === 3 ? { z: coordinates[2] } : {}), mode: shape.kind === "point" ? "markers" : shape.kind === "trajectory" ? "lines+markers" : "lines", connectgaps: false, line: { color: shape.color, width: 3, dash: shape.kind === "trajectory" ? "dash" : "solid" }, marker: { color: shape.color, size: shape.kind === "point" ? 8 : 3 } } as Data;
    });
    const axis = (title: string) => ({ title: { text: title }, range: [-bound, bound] as [number, number], gridcolor: "#343b43", zerolinecolor: "#73818d" });
    const layout: Partial<Layout> = { autosize: true, height: 460, paper_bgcolor: "#11151b", plot_bgcolor: "#11151b", font: { color: "#edf3f5" }, margin: { t: 24, r: 20, b: 80, l: 52 }, legend: { orientation: "h", y: -0.2 }, xaxis: { ...axis("x1"), constrain: "domain" }, yaxis: { ...axis("x2"), scaleanchor: "x", scaleratio: 1 }, scene: { xaxis: axis("x1"), yaxis: axis("x2"), zaxis: axis("x3"), aspectmode: "cube" } };
    const drawing = Plotly.newPlot(element, data, layout, { responsive: true, displaylogo: false, scrollZoom: false });
    drawing.then(() => { if (canceled) Plotly.purge(element); else setReady(true); }).catch(() => { if (!canceled) setFailure(true); });
    const observer = new ResizeObserver(() => { if (!canceled) void drawing.then(() => { if (!canceled) void Plotly.Plots.resize(element); }).catch(() => {}); });
    observer.observe(container);
    return () => { canceled = true; observer.disconnect(); Plotly.purge(element); element.remove(); };
  }, [geometry]);
  return <><p role="status">{failure ? "The interactive plot could not be displayed. The algebraic result and equation descriptions remain available; 3D requires WebGL." : ready ? "Interactive geometry ready" : "Drawing geometry…"}</p><div ref={host} className="geometry-canvas" role="img" aria-label={`${geometry.dimension}D equation geometry, ${geometry.classification} system`} /></>;
}
