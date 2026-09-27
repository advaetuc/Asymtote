import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";
import Home from "../../app/page";

test("the landing page exposes the Augmentr heading and method primer link", () => {
  render(<Home />);
  expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("Augmentr");
  expect(screen.getByRole("link", { name: "Augmentr home" })).toHaveTextContent("Augmentr");
  expect(screen.getByRole("link", { name: /New to these methods/ })).toHaveAttribute("href", "/learn");
  expect(screen.getByRole("link", { name: /Start solving/ })).toHaveAttribute("href", "/solve");
  expect(screen.getByText("Build an augmented matrix, pick a method, watch it get solved one row operation at a time.")).toBeInTheDocument();
  expect(screen.getAllByRole("article")).toHaveLength(3);
});
