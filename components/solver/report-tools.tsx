"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { reportJSON, reportLatex, reportMarkdown, type ReportInput } from "../../lib/reports/render";

const Preview = dynamic(() => import("./report-preview"), { loading: () => <p role="status">Preparing the complete report…</p> });
export function ReportTools({ input }: { input: ReportInput }) {
  const [preview, setPreview] = useState(false);
  const [error, setError] = useState("");
  function download(format: "md" | "tex" | "json") {
    try {
      const value = format === "md" ? reportMarkdown(input) : format === "tex" ? reportLatex(input) : reportJSON(input);
      const url = URL.createObjectURL(new Blob([value], { type: `${format === "json" ? "application/json" : format === "tex" ? "application/x-tex" : "text/markdown"};charset=utf-8` }));
      const anchor = document.createElement("a");
      anchor.href = url; anchor.download = `tulya-${input.outcome.result.method}-report.${format}`;
      document.body.append(anchor); anchor.click(); anchor.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      setError("");
    } catch { setError("The report could not be downloaded. Please retry, or use the printable report."); }
  }
  return <section className="report-tools"><h3>Reports &amp; downloads</h3><p>Exports include the original system, settings, analysis, complete trace, and diagnostics. JSON retains full returned precision; exact rationals remain exact in Markdown and LaTeX.</p><div className="action-row"><button onClick={() => download("md")}>Download Markdown</button><button onClick={() => download("tex")}>Download LaTeX</button><button onClick={() => download("json")}>Download JSON</button><button aria-expanded={preview} onClick={() => setPreview(v => !v)}>{preview ? "Close printable report" : "Open printable report"}</button></div>{error && <p role="alert">{error}</p>}{preview && <><p>The printable report contains every step, including history pages not currently visible in the inspector.</p><Preview input={input} /></>}</section>;
}
