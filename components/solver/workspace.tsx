"use client";

import { useEffect, useReducer, useRef, useState } from "react";
import { ApiError, analyzeSystem, solveSystem } from "../../lib/api/client";
import type { Method } from "../../lib/api/types";
import { serverCellErrors, validateGrid, type CellErrors } from "../../lib/solver/grid";
import { PRESETS } from "../../lib/solver/presets";
import { initialDraft, initialState, reducer, solveRequest, type Draft } from "../../lib/solver/state";
import { loadDraft, saveDraft } from "../../lib/solver/storage";
import { AnalysisPanel } from "./analysis-panel";
import { Configuration, configurationIssues } from "./configuration";
import { MatrixGrid } from "./matrix-grid";
import { ResultInspector } from "./result-inspector";

const stageLabels = { DIMENSIONS: "Choose dimensions", MATRIX_INPUT: "Enter equations", ANALYZING: "Analyzing the system…", METHOD_SELECTION: "Analysis ready. Choose a method.", METHOD_CONFIGURATION: "Configure your method", SOLVING: "Solving the system…", RESULTS: "Result ready" };

export function SolverWorkspace() {
  const [state, dispatch] = useReducer(reducer, initialState);
  const [errors, setErrors] = useState<CellErrors>({});
  const [preset, setPreset] = useState("");
  const [dimensions, setDimensions] = useState({ m: 2, n: 2 });
  const pending = useRef<{ id: number; controller: AbortController } | null>(null);
  const sequence = useRef(0);
  const busy = state.stage === "ANALYZING" || state.stage === "SOLVING";
  const { draft } = state;

  useEffect(() => {
    dispatch({ type: "RESTORE", draft: loadDraft() });
    return () => { pending.current?.controller.abort(); pending.current = null; };
  }, []);
  useEffect(() => {
    if (!state.restored) return;
    const timer = setTimeout(() => saveDraft(draft), 250);
    return () => clearTimeout(timer);
  }, [draft, state.restored]);
  useEffect(() => {
    if (!state.outcome) return;
    const heading = document.getElementById("result-title");
    heading?.focus({ preventScroll: true });
    heading?.scrollIntoView?.({ block: "start" });
  }, [state.outcome]);

  function abort() { pending.current?.controller.abort(); pending.current = null; }
  function edit(patch: Partial<Draft>, invalidateAnalysis = false) {
    if (!Object.keys(patch).every(k => k === "display")) abort();
    setErrors({});
    dispatch({ type: "EDIT", patch, invalidateAnalysis });
  }
  function chooseMethod(method: Method) { edit({ method, risk: false }); }
  async function run(kind: "analyze" | "solve") {
    const invalid = validateGrid(draft.system); setErrors(invalid);
    if (Object.keys(invalid).length) return;
    if (kind === "solve" && configurationIssues(draft).length) return;
    abort();
    const id = ++sequence.current, controller = new AbortController(); pending.current = { id, controller };
    dispatch({ type: "STAGE", stage: kind === "analyze" ? "ANALYZING" : "SOLVING" });
    try {
      if (kind === "analyze") {
        const outcome = await analyzeSystem({ system: draft.system, arithmetic_mode: draft.mode }, controller.signal);
        if (pending.current?.id === id) dispatch({ type: "ANALYZED", outcome });
      } else {
        const outcome = await solveSystem(solveRequest(draft), controller.signal);
        if (pending.current?.id === id) dispatch({ type: "SOLVED", outcome });
      }
    } catch (error) {
      if (pending.current?.id !== id || controller.signal.aborted) return;
      const failure = error instanceof ApiError ? error : new ApiError("Unable to complete the request. Please try again.", "network", "unavailable");
      setErrors(serverCellErrors(failure.details, draft.system.a[0]!.length));
      dispatch({ type: "FAILED", error: failure, stage: kind === "analyze" ? "MATRIX_INPUT" : "METHOD_CONFIGURATION" });
    } finally { if (pending.current?.id === id) pending.current = null; }
  }
  const eligibility = state.analysis?.status === "analyzed" ? state.analysis.methods.find(m => m.method === draft.method) : undefined;
  const canSolve = eligibility?.eligible && !configurationIssues(draft).length;
  const n = draft.system.a[0]!.length, m = draft.system.a.length;
  return <div className="solver-workflow">
    <div className="workspace-heading"><div><p className="eyebrow">Linear systems / Working notebook</p><h1>Make every<br /><span>step count.</span></h1></div><p className="lead">Enter your equations. Compare the methods. Follow the reasoning all the way to the result.</p></div>
    <div className="workflow-status" role="status" aria-live="polite"><span className={busy ? "busy-dot" : "status-dot"} aria-hidden="true" />{stageLabels[state.stage]}{busy && <button onClick={() => { const stage = state.stage === "ANALYZING" ? "MATRIX_INPUT" : "METHOD_CONFIGURATION"; abort(); dispatch({ type: "CANCEL", stage }); }}>Cancel request</button>}</div>
    <section className="panel" aria-labelledby="matrix-title"><div className="panel-heading"><div><p className="eyebrow">01 / Define the problem</p><h2 id="matrix-title">Your augmented matrix</h2></div><label className="preset-select">Explore an example<select value={preset} onChange={e => {
      const selected = PRESETS.find(p => p.id === e.target.value); if (!selected) return;
      abort(); setErrors({}); setPreset(selected.id);
      dispatch({ type: "PRESET", draft: { ...initialDraft, display: draft.display, system: structuredClone(selected.system), method: selected.method, guess: selected.system.a[0]!.map(() => "0"), dominance: selected.reorder ?? true } });
    }}><option value="">Choose a preset…</option>{PRESETS.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}</select></label></div>
      {preset && <p className="info-banner">{PRESETS.find(p => p.id === preset)?.note}</p>}
      <div className="control-row"><label>Equations<select value={state.stage === "DIMENSIONS" ? dimensions.m : m} onChange={e => {
        const value = Number(e.target.value); abort(); setErrors({}); setPreset("");
        if (state.stage === "DIMENSIONS") setDimensions(d => ({ ...d, m: value }));
        else dispatch({ type: "RESIZE", m: value, n });
      }}>{Array.from({ length: 12 }, (_, i) => <option key={i} value={i + 1}>{i + 1}</option>)}</select></label>
      <label>Unknowns<select value={state.stage === "DIMENSIONS" ? dimensions.n : n} onChange={e => {
        const value = Number(e.target.value); abort(); setErrors({}); setPreset("");
        if (state.stage === "DIMENSIONS") setDimensions(d => ({ ...d, n: value }));
        else dispatch({ type: "RESIZE", m, n: value });
      }}>{Array.from({ length: 12 }, (_, i) => <option key={i} value={i + 1}>{i + 1}</option>)}</select></label>
      <label>Arithmetic<select value={draft.mode} onChange={e => edit({ mode: e.target.value as Draft["mode"], method: e.target.value === "exact" && (draft.method === "jacobi" || draft.method === "gauss_seidel") ? "gaussian" : draft.method, risk: false }, true)}><option value="float64">Float64 · all methods</option><option value="exact">Exact rational · direct methods</option></select></label></div>
      {state.stage === "DIMENSIONS" ? <button className="primary-button" onClick={() => dispatch({ type: "RESIZE", ...dimensions })}>Create matrix</button> : <>
        <MatrixGrid system={draft.system} errors={errors} onChange={system => { setPreset(""); edit({ system, risk: false }, true); }} />
        <div className="action-row"><button className="primary-button" disabled={busy} onClick={() => run("analyze")}>Analyze system</button><button disabled={busy} onClick={() => { setPreset(""); edit({ system: { a: draft.system.a.map(row => row.map(() => "")), b: draft.system.b.map(() => "") }, risk: false }, true); }}>Clear entries</button><span className="muted">{m} equations · {n} unknowns · draft saved for this tab</span></div>
        {!!Object.keys(errors).length && <p role="alert" className="error-note">Correct the highlighted matrix cells before continuing.</p>}
      </>}
    </section>
    {state.error && <section role="alert" className="panel error-note"><h2>{state.error.status === 422 ? "Check your input" : state.error.status === 500 ? "The solver encountered an error" : "Request could not be completed"}</h2><p>{state.error.message}</p>{state.error.details.map((issue, i) => <p key={i}>{issue.location.join(" → ")}: {issue.message}</p>)}<p>Request {state.error.requestId}</p><button onClick={() => run(state.stage === "METHOD_CONFIGURATION" ? "solve" : "analyze")}>Retry request</button></section>}
    {state.analysis && <div className="workspace-columns"><div><AnalysisPanel analysis={state.analysis} method={draft.method} onSelect={chooseMethod} />{state.analysis.status === "analyzed" && <><Configuration draft={draft} onChange={patch => edit(patch)} /><div className="solve-action"><button className="primary-button" disabled={!canSolve || busy} onClick={() => run("solve")}>Solve system</button>{eligibility && !eligibility.eligible && <p className="warning-note">{eligibility.reason}</p>}</div></>}</div>
      <div className="result-column"><section className="panel display-panel"><h2>Display preferences</h2><div className="control-row"><label>Number display<select value={draft.display.mode} onChange={e => edit({ display: { ...draft.display, mode: e.target.value as Draft["display"]["mode"] } })}><option value="decimal">Decimals</option><option value="fraction">Fractions</option></select></label><label>Decimal places<select value={draft.display.decimal_places} onChange={e => edit({ display: { ...draft.display, decimal_places: Number(e.target.value) } })}>{Array.from({ length: 13 }, (_, i) => <option key={i} value={i}>{i}</option>)}</select></label></div><p className="muted">Changes presentation only. No recalculation is needed.</p></section>
      {state.outcome ? <ResultInspector outcome={state.outcome} display={draft.display} analysis={state.analysis} /> : <div className="result-placeholder panel"><span aria-hidden="true">A x = b</span><h2>{busy ? "Calculation in progress" : "The reasoning appears here"}</h2><p>Choose a method and solve to reveal the answer, steps, and diagnostics.</p></div>}</div>
    </div>}
  </div>;
}
