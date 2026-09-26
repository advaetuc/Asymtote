import { StrictMode } from "react";
import { act, render, screen } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";
import GeometryPlot from "../../components/solver/geometry-plot";
import { deriveGeometry } from "../../lib/geometry/derive";
import type { CompletedSolve } from "../../lib/reports/render";
import fixtures from "./fixtures/api.json";

const plot = vi.hoisted(() => ({ newPlot: vi.fn(), purge: vi.fn(), register: vi.fn(), Plots: { resize: vi.fn() } }));
vi.mock("plotly.js/lib/core", () => ({ default: plot }));
vi.mock("plotly.js/lib/scatter", () => ({ default: {} }));
vi.mock("plotly.js/lib/scatter3d", () => ({ default: {} }));
vi.mock("plotly.js/lib/mesh3d", () => ({ default: {} }));
afterEach(() => { vi.unstubAllGlobals(); vi.clearAllMocks(); });

test("late completion from a Strict Mode remount cannot erase the current plot", async () => {
  vi.stubGlobal("ResizeObserver", class { observe() {} disconnect() {} });
  const completions: (() => void)[] = [];
  plot.newPlot.mockImplementation(() => new Promise<void>(resolve => completions.push(resolve)));
  const { unmount } = render(<StrictMode><GeometryPlot geometry={deriveGeometry(fixtures.jacobi as CompletedSolve)!} /></StrictMode>);
  const oldNode = plot.newPlot.mock.calls[0]![0] as HTMLElement;
  const currentNode = plot.newPlot.mock.calls[1]![0] as HTMLElement;
  expect(oldNode).not.toBe(currentNode); expect(oldNode.isConnected).toBe(false); expect(currentNode.isConnected).toBe(true);
  await act(async () => { completions[1]!(); });
  await screen.findByText("Interactive geometry ready");
  await act(async () => { completions[0]!(); });
  expect(plot.purge.mock.calls.some(([node]) => node === currentNode)).toBe(false);
  unmount(); expect(plot.purge.mock.calls.some(([node]) => node === currentNode)).toBe(true);
});
test("plot failures leave a clear fallback", async () => {
  vi.stubGlobal("ResizeObserver", class { observe() {} disconnect() {} });
  plot.newPlot.mockRejectedValue(new Error("WebGL unavailable"));
  render(<GeometryPlot geometry={deriveGeometry(fixtures.gaussian as CompletedSolve)!} />);
  expect(await screen.findByText(/interactive plot could not be displayed/)).toBeInTheDocument();
});
