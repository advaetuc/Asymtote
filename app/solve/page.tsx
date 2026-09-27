import type { Metadata } from "next";
import { SiteHeader } from "../../components/site-header";
import { SolverWorkspace } from "../../components/solver/workspace";
import { FOOTER_COPY } from "../../components/site-copy";

export const metadata: Metadata = { title: "Solver workspace — Augmentr" };
export default function SolvePage() {
  return <main id="main" className="page-shell"><SiteHeader /><SolverWorkspace /><footer>{FOOTER_COPY}</footer></main>;
}
