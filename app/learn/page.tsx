import type { Metadata } from "next";
import Link from "next/link";
import { SiteHeader } from "../../components/site-header";
import { FOOTER_COPY } from "../../components/site-copy";

export const metadata: Metadata = { title: "How these methods work — Augmentr" };

export default function LearnPage() {
  return <main id="main" className="page-shell"><SiteHeader />
    <section className="intro"><p className="eyebrow">Linear systems / Methods</p><h1>How these methods work</h1><p className="lead">A short primer before you touch a matrix. Skip ahead if you already know rank, elimination, and convergence.</p><Link href="/solve" className="primary-link">Start solving →</Link></section>
    <section className="panel"><h2>What &quot;solving&quot; means here</h2><p>A linear system is an augmented matrix — coefficients on the left, right-hand-side values on the right. Solving it means finding the values that satisfy every row at once, or showing precisely why no such values exist, or why more than one set of values does.</p><p>Enter linear equation coefficients and right-hand-side values in the solver.</p></section>
    <section className="panel"><h2>Direct methods</h2>
      <h3>Gaussian elimination</h3><p>Reduces the augmented matrix to row-echelon form using partial pivoting, then back-substitutes. Deterministic, finishes in a fixed number of steps, and is the reference method for square, well-posed systems.</p>
      <h3>Gauss–Jordan elimination</h3><p>Continues past row-echelon form to reduced row-echelon form (RREF), reading the solution — or the parametric form of infinitely many solutions — directly off the final matrix.</p>
      <p className="muted">Partial pivoting applies in float64 mode. Exact mode uses rational row operations. Both direct methods also support rectangular systems, subject to resource limits.</p>
    </section>
    <section className="panel"><h2>Iterative methods</h2>
      <h3>Jacobi iteration</h3><p>Starts from an initial guess and repeatedly refines every variable using the <em>previous</em> iteration&apos;s values, all at once. Converges when the iteration matrix&apos;s spectral radius is under 1 — not guaranteed for every system, and the app tells you the spectral radius before you run it.</p>
      <h3>Gauss–Seidel iteration</h3><p>Same idea as Jacobi, but each variable update uses the <em>newest</em> values already computed in the current sweep. Usually converges faster than Jacobi when it converges at all, but &quot;usually&quot; is not &quot;always&quot; — Augmentr won&apos;t claim one method is faster than the other as a general rule, only for the matrix in front of you.</p>
      <p className="muted">Spectral radius is a floating diagnostic and may be unavailable. Compare the returned histories for your system; no speed ranking is implied by method availability.</p>
    </section>
    <section className="panel"><h2>Why a system might not have one clean answer</h2><p>Rank tells the story. If the coefficient matrix and the augmented matrix have the same rank, and that rank equals the number of unknowns, there&apos;s exactly one solution. If the ranks match but fall short of the unknown count, there are infinitely many — described by free parameters. If the ranks don&apos;t match, no solution satisfies every row simultaneously. Augmentr classifies your system this way before offering you a method, not after you&apos;ve run one and gotten a strange answer.</p></section>
    <section className="panel"><h2>Diagonal dominance, briefly</h2><p>Strict diagonal dominance guarantees Jacobi and Gauss–Seidel will converge — but it&apos;s a sufficient condition, not a necessary one. Plenty of systems that aren&apos;t diagonally dominant still converge fine. Augmentr can attempt to reorder your equations (not your variables) into a diagonally dominant arrangement if one exists, and will always show you which reordering it used — your original system is never silently replaced.</p><p className="muted">Iteration uses unrounded float64 values and requires both backward error and normalized step change to meet the tolerance. SPD is sufficient for Gauss–Seidel, but does not by itself guarantee Jacobi convergence.</p></section>
    <footer>{FOOTER_COPY}</footer>
  </main>;
}
