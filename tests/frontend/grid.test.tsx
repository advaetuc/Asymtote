import { useState } from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, test } from "vitest";
import { MatrixGrid } from "../../components/solver/matrix-grid";
import { pasteBlock, resizeSystem, serverCellErrors, tokenIssue, validateGrid } from "../../lib/solver/grid";

const blank = { a: [["", ""], ["", ""]], b: ["", ""] };
function Editor() { const [system, setSystem] = useState(blank); return <MatrixGrid system={system} onChange={setSystem} errors={{}} />; }

test("resizing keeps compatible coefficients and RHS separately", () => {
  const system = { a: [["1", "2"], ["3", "4"]], b: ["5", "6"] };
  expect(resizeSystem(system, 3, 1)).toEqual({ a: [["1"], ["3"], [""]], b: ["5", "6", ""] });
  expect(resizeSystem(system, 1, 3)).toEqual({ a: [["1", "2", ""]], b: ["5"] });
});
test.each(["", " 1", "1 ", "1+2", "1/0", "NaN", "1e101", "１", "1".repeat(49)])("rejects invalid token %s", value => expect(tokenIssue(value)).toBeTruthy());
test.each(["1", "-2/3", "1/-3", ".5", "1.", "-1.4e-100"])("accepts token grammar %s", value => expect(tokenIssue(value)).toBeUndefined());
test("backend magnitude decisions are not duplicated through JS rounding", () => expect(tokenIssue("1000000000000.000000000000001")).toBeUndefined());
test("bulk paste is atomic and includes RHS", () => {
  expect(pasteBlock(blank, "1\t2\t3\r\n4\t5\t6\r\n", 0, 0)).toEqual({ a: [["1", "2"], ["4", "5"]], b: ["3", "6"] });
  expect(() => pasteBlock(blank, "1\t2\n3", 0, 0)).toThrow(/rectangular/);
  expect(() => pasteBlock(blank, "1\t2\t3", 1, 1)).toThrow(/does not fit/);
  expect(blank.b).toEqual(["", ""]);
});
test("maps API cell locations even through method union paths", () => {
  expect(serverCellErrors([{ code: "invalid", message: "Bad coefficient", location: ["body", "jacobi", "system", "a", 0, 1] }, { code: "invalid", message: "Bad RHS", location: ["body", "system", "b", 1] }], 2)).toEqual({ "0:1": "Bad coefficient", "1:2": "Bad RHS" });
});
test("arrow and tab navigation follow augmented matrix order", async () => {
  const user = userEvent.setup(); render(<Editor />);
  const first = screen.getByLabelText("Row 1, x1"); first.focus();
  await user.keyboard("{ArrowRight}"); expect(screen.getByLabelText("Row 1, x2")).toHaveFocus();
  await user.keyboard("{ArrowDown}"); expect(screen.getByLabelText("Row 2, x2")).toHaveFocus();
  await user.keyboard("{ArrowLeft}{ArrowUp}"); expect(first).toHaveFocus();
  await user.tab(); expect(screen.getByLabelText("Row 1, x2")).toHaveFocus();
  await user.tab(); expect(screen.getByLabelText("Row 1, right-hand side")).toHaveFocus();
  await user.tab(); expect(screen.getByLabelText("Row 2, x1")).toHaveFocus();
  await user.tab({ shift: true }); expect(screen.getByLabelText("Row 1, right-hand side")).toHaveFocus();
});
test("paste updates cells and rejects overflow without changing input", () => {
  render(<Editor />); const first = screen.getByLabelText("Row 1, x1");
  fireEvent.paste(first, { clipboardData: { getData: () => "1\t2\t3\n4\t5\t6" } });
  expect(screen.getByLabelText("Row 2, right-hand side")).toHaveValue("6");
  fireEvent.paste(first, { clipboardData: { getData: () => "1\t2\t3\t4" } });
  expect(screen.getByRole("alert")).toHaveTextContent(/does not fit/); expect(first).toHaveValue("1");
});
test("invalid cells have text and programmatic error descriptions", () => {
  render(<MatrixGrid system={blank} onChange={() => {}} errors={validateGrid(blank)} />);
  const cell = screen.getByLabelText("Row 1, x1");
  expect(cell).toHaveAttribute("aria-invalid", "true"); expect(cell).toHaveAccessibleDescription("Enter a number.");
});
