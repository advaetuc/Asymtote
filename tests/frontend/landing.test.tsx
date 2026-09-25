import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";
import Home from "../../app/page";

test("the landing page exposes a meaningful heading and a working method anchor", () => {
  render(<Home />);
  expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("Linear equations,understood.");
  const link = screen.getByRole("link", { name: /Explore the four methods/ });
  expect(link).toHaveAttribute("href", "#methods");
  expect(document.querySelector(link.getAttribute("href")!)).toBeInTheDocument();
  expect(screen.getAllByRole("article")).toHaveLength(4);
});
