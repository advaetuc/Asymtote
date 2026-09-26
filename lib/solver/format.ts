import type { Display, Numeric } from "../api/types";

export const rawValue = (value: Numeric): string => typeof value === "number" ? String(value) : `${value.numerator}/${value.denominator}`;

function exactDecimal(numerator: string, denominator: string, places: number): string {
  const n = BigInt(numerator), d = BigInt(denominator), zero = BigInt(0);
  const scale = BigInt(10) ** BigInt(places);
  const absolute = n < zero ? -n : n;
  const scaled = absolute * scale;
  const rounded = scaled / d + (scaled % d * BigInt(2) >= d ? BigInt(1) : zero);
  const digits = rounded.toString().padStart(places + 1, "0");
  const text = places ? `${digits.slice(0, -places)}.${digits.slice(-places)}` : digits;
  const sign = n < zero && rounded !== zero ? "−" : "";
  return `${scaled % d === zero ? "" : "≈ "}${sign}${text}`;
}

function approximateFraction(value: number, places: number): string {
  if (value === 0) return "≈ 0";
  let x = Math.abs(value), h0 = 0, h1 = 1, k0 = 1, k1 = 0;
  for (let i = 0; i < 64; i++) {
    const a = Math.floor(x), h = a * h1 + h0, k = a * k1 + k0;
    if (k > 10000 || !Number.isSafeInteger(h) || !Number.isSafeInteger(k)) break;
    [h0, h1, k0, k1] = [h1, h, k1, k];
    const remainder = x - a;
    if (remainder === 0) break;
    x = 1 / remainder;
  }
  if (!k1 || !h1) return `≈ ${decimalFloat(value, places)}`;
  return `≈ ${value < 0 ? "−" : ""}${h1}${k1 === 1 ? "" : `/${k1}`}`;
}

function decimalFloat(value: number, places: number): string {
  if (value !== 0 && (Math.abs(value) >= 1e9 || Math.abs(value) < 10 ** -places)) return value.toExponential(Math.min(places, 12));
  return value.toFixed(places);
}

export function formatValue(value: Numeric, display: Display): string {
  if (typeof value === "number") return display.mode === "fraction" ? approximateFraction(value, display.decimal_places) : decimalFloat(value, display.decimal_places);
  if (display.mode === "fraction") return value.denominator === "1" ? value.numerator : `${value.numerator}/${value.denominator}`;
  return exactDecimal(value.numerator, value.denominator, display.decimal_places);
}
export const metric = (value: number | null | undefined) => value == null ? "Unavailable" : value === 0 ? "0" : value.toExponential(3);
export function isZero(value: Numeric): boolean { return typeof value === "number" ? value === 0 : BigInt(value.numerator) === BigInt(0); }
