// The AD stack the user is editing: component and parameter overrides per layer. Shared by the workbench,
// the research page and the architecture view (session storage).
import type { LayerSpec } from "./api";
import { usePersistentState } from "./hooks";

export type StackEdit = Record<string, { component: string; paramsText: string }>;

export function useStack(): [StackEdit, (s: StackEdit) => void] {
  return usePersistentState<StackEdit>("me.workbench.stack", {});
}

// Parses the JSON parameter overrides; returns the layer whose JSON is invalid instead of throwing.
export function stackSpecs(stack: StackEdit): { specs: Record<string, LayerSpec>; invalid: string | null } {
  const specs: Record<string, LayerSpec> = {};
  for (const [layer, edit] of Object.entries(stack)) {
    if (!edit.component) continue;
    let params: Record<string, unknown> | undefined;
    if (edit.paramsText.trim()) {
      try {
        const parsed: unknown = JSON.parse(edit.paramsText);
        if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) return { specs, invalid: layer };
        params = parsed as Record<string, unknown>;
      } catch {
        return { specs, invalid: layer };
      }
    }
    specs[layer] = { component: edit.component, ...(params && Object.keys(params).length ? { params } : {}) };
  }
  return { specs, invalid: null };
}
