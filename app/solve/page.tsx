import type { Metadata } from "next";
import { SiteHeader } from "../../components/site-header";
import { SolverWorkspace } from "../../components/solver/workspace";

export const metadata: Metadata = { title: "Solver workspace — TULYA" };
export default function SolvePage() {
  return <main id="main" className="page-shell"><SiteHeader /><SolverWorkspace /><footer>Precision in calculation. Clarity in explanation.</footer></main>;
}
