"use client";

import { Component, useMemo, useState, type ReactNode } from "react";
import dynamic from "next/dynamic";
import { deriveGeometry } from "../../lib/geometry/derive";
import type { CompletedSolve } from "../../lib/reports/render";

const Plot = dynamic(() => import("./geometry-plot"), { ssr: false, loading: () => <p role="status">Loading interactive geometry…</p> });
class PlotBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  render() { return this.state.failed ? <p role="alert">Geometry could not load. Close and reopen the view to retry; the solver result remains available.</p> : this.props.children; }
}
export function GeometryPanel({ outcome }: { outcome: CompletedSolve }) {
  const [open, setOpen] = useState(false);
  const geometry = useMemo(() => deriveGeometry(outcome), [outcome]);
  const boundLabel = geometry ? Number(geometry.bound.toPrecision(4)).toString() : "";
  return <section className="geometry-panel"><h3>Visualize</h3><p>A 2D line or 3D plane for two- or three-unknown square systems; a convergence plot in Steps for iterative methods.</p>{!geometry ? <p>A 2D or 3D plot only applies to 2 × 2 or 3 × 3 systems. This system has {outcome.problem.shape.equations} equations and {outcome.problem.shape.unknowns} unknowns; see Diagnostics and Steps for the equivalent algebraic description.</p> : <><p>Explore the original equations in {geometry.dimension}D. Drag to {geometry.dimension === 3 ? "rotate" : "select a zoom region"}; use the plot toolbar to pan, zoom, or reset. Select legend entries to distinguish coincident equations. The text and trace remain the keyboard-accessible explanation.</p><button aria-expanded={open} onClick={() => setOpen(v => !v)}>{open ? "Hide geometry" : "Show geometry"}</button>{open && <div className="geometry-content"><p>Backend classification: <strong>{geometry.classification}</strong>. Displayed axes: −{boundLabel} to {boundLabel}.</p>{geometry.notes.map(note => <p className="muted" key={note}>{note}</p>)}<PlotBoundary><Plot geometry={geometry} /></PlotBoundary></div>}</>}</section>;
}

