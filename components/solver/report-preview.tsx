"use client";

import katex from "katex";
import "katex/dist/katex.min.css";
import { reportBlocks, type ReportInput } from "../../lib/reports/render";

export default function ReportPreview({ input }: { input: ReportInput }) {
  return <><button onClick={() => window.print()}>Print / Save as PDF</button><article className="report-preview" aria-label="Complete printable report">{reportBlocks(input).map((block, i) => block.kind === "heading" ? <h3 key={i}>{block.text}</h3> : block.kind === "math" ? <div className="report-math" key={i} dangerouslySetInnerHTML={{ __html: katex.renderToString(block.text, { displayMode: true, trust: false, throwOnError: false, strict: "error", output: "htmlAndMathml" }) }} /> : <p key={i}>{block.text}</p>)}</article></>;
}
