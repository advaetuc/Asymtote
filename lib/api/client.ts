import type { AnalyzeOutcome, AnalyzeRequest, Model, SolveOutcome, SolveRequest } from "./types";
import { validResponse } from "./validate-response";

export class ApiError extends Error {
  constructor(message: string, readonly kind: "http" | "network" | "protocol",
    readonly requestId: string, readonly status?: number, readonly details: Model<"Issue">[] = []) {
    super(message);
    this.name = "ApiError";
  }
}

async function post<T>(route: "analyze" | "solve", payload: AnalyzeRequest | SolveRequest, signal: AbortSignal): Promise<T> {
  const requestId = crypto.randomUUID();
  let response: Response;
  try {
    response = await fetch(`/api/v1/${route}`, {
      method: "POST", headers: { "Content-Type": "application/json", "X-Request-ID": requestId },
      body: JSON.stringify(payload), signal, cache: "no-store",
    });
  } catch (error) {
    if (signal.aborted) throw error;
    throw new ApiError("Could not reach the solver. Check your connection and try again.", "network", requestId);
  }
  const id = response.headers.get("x-request-id") || requestId;
  let data: unknown;
  try { data = await response.json(); }
  catch (error) {
    if (signal.aborted) throw error;
    throw new ApiError("The server returned an unreadable response. Please retry.", "protocol", id, response.status);
  }
  if (!response.ok) {
    if (validResponse(data, "ErrorResponse")) {
      const body = data as Model<"ErrorResponse">;
      throw new ApiError(body.error.message, "http", id, response.status,
        body.details.length ? body.details : [body.error]);
    }
    throw new ApiError("The server could not complete this request. Please retry.", "http", id, response.status);
  }
  if (!validResponse(data, route === "analyze" ? "AnalyzeOutcome" : "SolveOutcome")) {
    throw new ApiError("The response does not match the solver contract. Please retry.", "protocol", id, response.status);
  }
  return { ...(data as object), request_id: id } as T;
}

export const analyzeSystem = (request: AnalyzeRequest, signal: AbortSignal) => post<AnalyzeOutcome>("analyze", request, signal);
export const solveSystem = (request: SolveRequest, signal: AbortSignal) => post<SolveOutcome>("solve", request, signal);
