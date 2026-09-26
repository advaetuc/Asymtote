import { afterEach, describe, expect, test, vi } from "vitest";
import { analyzeSystem, ApiError, solveSystem } from "../../lib/api/client";
import { validResponse } from "../../lib/api/validate-response";
import fixtures from "./fixtures/api.json";

afterEach(() => vi.unstubAllGlobals());
const request = { system: { a: [["1"]], b: ["1"] }, method: "gaussian" as const };

describe("generated runtime contract", () => {
  test.each(Object.entries(fixtures))("accepts authentic backend fixture %s", (name, data) => {
    expect(validResponse(data, name.startsWith("analysis") ? "AnalyzeOutcome" : "SolveOutcome")).toBe(true);
  });
  test("rejects malformed nested data and undeclared fields", () => {
    const invalid = structuredClone(fixtures.gaussian);
    invalid.result.solution = [NaN, 1];
    expect(validResponse(invalid, "SolveOutcome")).toBe(false);
    expect(validResponse({ ...fixtures.gaussian, unexpected: true }, "SolveOutcome")).toBe(false);
    expect(validResponse({ status: "completed" }, "SolveOutcome")).toBe(false);
  });
});

test("sends string tokens, signal, and correlation ID without rounding", async () => {
  const fetcher = vi.fn().mockResolvedValue(new Response(JSON.stringify(fixtures.exact), { headers: { "x-request-id": "server-id" } }));
  vi.stubGlobal("fetch", fetcher);
  const signal = new AbortController().signal;
  const result = await solveSystem({ ...request, options: { arithmetic_mode: "exact" } }, signal);
  expect(result.request_id).toBe("server-id");
  expect(fetcher).toHaveBeenCalledWith("/api/v1/solve", expect.objectContaining({ signal, method: "POST", cache: "no-store" }));
  const options = fetcher.mock.calls[0]![1] as RequestInit;
  expect(JSON.parse(options.body as string).system.a).toEqual([["1"]]);
  expect((options.headers as Record<string, string>)["X-Request-ID"]).toBeTruthy();
});

test.each(["declined", "limit", "breakdown", "inconsistent"] as const)("HTTP 200 %s remains a mathematical result", async name => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify(fixtures[name]))));
  expect((await solveSystem(request, new AbortController().signal)).status).toBe("completed");
});

test.each([422, 500])("maps structured HTTP %i errors with safe details", async status => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ status: "error", request_id: "id", error: { code: "problem", message: "Please correct the request.", location: [] }, details: [{ code: "invalid_token", message: "Invalid number", location: ["body", "system", "a", 0, 0] }] }), { status, headers: { "x-request-id": "problem-id" } })));
  await expect(solveSystem(request, new AbortController().signal)).rejects.toMatchObject({ kind: "http", status, requestId: "problem-id", details: [expect.objectContaining({ code: "invalid_token" })] });
});

test("network failure and unreadable responses remain distinct", async () => {
  const fetcher = vi.fn().mockRejectedValueOnce(new TypeError("network")).mockResolvedValueOnce(new Response("<html>proxy error</html>")).mockResolvedValueOnce(new Response('{"bad":true}'));
  vi.stubGlobal("fetch", fetcher);
  await expect(analyzeSystem({ system: request.system }, new AbortController().signal)).rejects.toMatchObject({ kind: "network" });
  await expect(solveSystem(request, new AbortController().signal)).rejects.toMatchObject({ kind: "protocol" });
  await expect(solveSystem(request, new AbortController().signal)).rejects.toBeInstanceOf(ApiError);
});

test("cancellation is not rewritten as a network failure", async () => {
  const controller = new AbortController(); controller.abort();
  const error = new DOMException("Aborted", "AbortError");
  vi.stubGlobal("fetch", vi.fn().mockRejectedValue(error));
  await expect(solveSystem(request, controller.signal)).rejects.toBe(error);
});
