import Link from "next/link";

export function SiteHeader() {
  return <header className="masthead">
    <Link className="wordmark" href="/" aria-label="TULYA home">TULYA<span aria-hidden="true">.</span></Link>
    <nav aria-label="Main navigation"><Link href="/learn">Learn</Link><Link href="/solve">Solver workspace <span aria-hidden="true">↗</span></Link></nav>
  </header>;
}
