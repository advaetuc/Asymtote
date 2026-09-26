import { z } from "zod";
import type { Draft } from "./state";

export const DRAFT_KEY = "tulya.draft.v1";
// This is local editor state, not a second API contract. Incomplete cell tokens are allowed.
const draftSchema = z.object({
  system: z.object({ a: z.array(z.array(z.string().max(48)).min(1).max(12)).min(1).max(12), b: z.array(z.string().max(48)).min(1).max(12) }),
  method: z.enum(["gaussian", "gauss_jordan", "jacobi", "gauss_seidel"]), mode: z.enum(["exact", "float64"]),
  display: z.object({ mode: z.enum(["decimal", "fraction"]), decimal_places: z.number().int().min(0).max(12) }),
  guess: z.array(z.string().max(48)).min(1).max(12), tolerance: z.string().max(48), maxIterations: z.string().max(4),
  dominance: z.boolean(), nonzero: z.boolean(), risk: z.boolean(),
}).refine(d => d.system.b.length === d.system.a.length && d.system.a.every(row => row.length === d.system.a[0]!.length) && d.guess.length === d.system.a[0]!.length);

export function loadDraft(): Draft | null {
  try {
    const raw = sessionStorage.getItem(DRAFT_KEY);
    if (!raw || raw.length > 20000) return null;
    const parsed = draftSchema.safeParse(JSON.parse(raw));
    if (!parsed.success) return null;
    // Consent to convergence risk is always renewed for a restored session draft.
    return { ...parsed.data, risk: false };
  } catch { return null; }
}
export function saveDraft(draft: Draft): void {
  try { sessionStorage.setItem(DRAFT_KEY, JSON.stringify(draft)); } catch { /* Storage may be blocked; the editor still works. */ }
}
