// Runtime validation reads the generated OpenAPI, rather than duplicating API models.
import document from "../../docs/openapi.json";

type Schema = {
  $ref?: string; type?: string; const?: unknown; enum?: unknown[];
  anyOf?: Schema[]; oneOf?: Schema[]; allOf?: Schema[];
  required?: string[]; properties?: Record<string, Schema>; additionalProperties?: boolean;
  items?: Schema; prefixItems?: Schema[]; minItems?: number; maxItems?: number;
  minimum?: number; maximum?: number; exclusiveMinimum?: number;
  minLength?: number; maxLength?: number;
};
const schemas = document.components.schemas as Record<string, Schema>;

function matches(value: unknown, schema: Schema, depth = 0): boolean {
  if (depth > 64) return false;
  if (schema.$ref) {
    const target = schemas[schema.$ref.split("/").at(-1)!];
    return !!target && matches(value, target, depth + 1);
  }
  if (schema.const !== undefined && value !== schema.const) return false;
  if (schema.enum && !schema.enum.includes(value)) return false;
  if (schema.anyOf && !schema.anyOf.some(s => matches(value, s, depth + 1))) return false;
  if (schema.oneOf && schema.oneOf.filter(s => matches(value, s, depth + 1)).length !== 1) return false;
  if (schema.allOf && !schema.allOf.every(s => matches(value, s, depth + 1))) return false;
  switch (schema.type) {
    case "null": return value === null;
    case "boolean": return typeof value === "boolean";
    case "string": return typeof value === "string" && value.length >= (schema.minLength ?? 0) && value.length <= (schema.maxLength ?? Infinity);
    case "integer":
    case "number": return typeof value === "number" && Number.isFinite(value)
      && (schema.type !== "integer" || Number.isInteger(value))
      && value >= (schema.minimum ?? -Infinity) && value <= (schema.maximum ?? Infinity)
      && (schema.exclusiveMinimum === undefined || value > schema.exclusiveMinimum);
    case "array": return Array.isArray(value) && value.length >= (schema.minItems ?? 0)
      && value.length <= (schema.maxItems ?? Infinity)
      && value.every((v, i) => matches(v, schema.prefixItems?.[i] ?? schema.items ?? {}, depth + 1));
    case "object": {
      if (value === null || typeof value !== "object" || Array.isArray(value)) return false;
      const object = value as Record<string, unknown>;
      return (schema.required ?? []).every(key => Object.hasOwn(object, key))
        && Object.entries(object).every(([key, v]) => {
          const property = schema.properties?.[key];
          return property ? matches(v, property, depth + 1) : schema.additionalProperties !== false;
        });
    }
    default: return true;
  }
}

export function validResponse(value: unknown, name: "AnalyzeOutcome" | "SolveOutcome" | "ErrorResponse"): boolean {
  return matches(value, schemas[name]!);
}
