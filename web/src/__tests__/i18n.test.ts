// Translation completeness and the "no hardcoded UI strings" rule.
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

import { NAMESPACES, resources } from "../i18n";

const SRC = join(__dirname, "..");
type Tree = { [k: string]: string | Tree };

function flatten(tree: Tree, prefix = ""): Record<string, string> {
  const out: Record<string, string> = {};
  for (const [k, v] of Object.entries(tree)) {
    const key = prefix ? `${prefix}.${k}` : k;
    if (typeof v === "string") out[key] = v;
    else Object.assign(out, flatten(v, key));
  }
  return out;
}
function files(dir: string): string[] {
  return readdirSync(dir).flatMap((f) => {
    const p = join(dir, f);
    if (statSync(p).isDirectory()) return f === "__tests__" || f === "locales" ? [] : files(p);
    return p.endsWith(".tsx") || p.endsWith(".ts") ? [p] : [];
  });
}
const en = Object.fromEntries(NAMESPACES.map((ns) => [ns, flatten(resources.en[ns] as unknown as Tree)]));
const de = Object.fromEntries(NAMESPACES.map((ns) => [ns, flatten(resources.de[ns] as unknown as Tree)]));

describe("locales", () => {
  it.each(NAMESPACES)("namespace %s has the same keys in English and German", (ns) => {
    expect(Object.keys(de[ns]).sort()).toEqual(Object.keys(en[ns]).sort());
  });

  it.each(NAMESPACES)("namespace %s has no empty texts and keeps the interpolation variables", (ns) => {
    for (const [key, text] of Object.entries(en[ns])) {
      expect(text.trim(), `${ns}:${key}`).not.toBe("");
      expect(de[ns][key].trim(), `${ns}:${key}`).not.toBe("");
      const vars = (s: string) => (s.match(/\{\{\w+\}\}/g) ?? []).sort();
      expect(vars(de[ns][key]), `${ns}:${key}`).toEqual(vars(text));
    }
  });

  it("German differs from English where words are translated", () => {
    const same = Object.entries(en.app).filter(([k, v]) => de.app[k] === v && /[a-z]{4,}\s+[a-z]{4,}/i.test(v) && !PROPER_NAMES.includes(k));
    expect(same.map(([k]) => k)).toEqual([]);
  });
});

// proper names that are the same in every language
const BRAND = ["Motion", "Engine", "MotionEngine"];
const PROPER_NAMES = ["controllers.pure_pursuit", "controllers.stanley"];

describe("source code", () => {
  const sources = files(SRC);

  it("every literal translation key used in the code exists", () => {
    const missing: string[] = [];
    for (const file of sources) {
      const code = readFileSync(file, "utf8");
      const nsMatch = code.match(/useTranslation\(\s*(\[[^\]]*\]|"[^"]*")?\s*\)/);
      const nsList: string[] = nsMatch?.[1] ? JSON.parse(nsMatch[1]) instanceof Array ? JSON.parse(nsMatch[1]) : [JSON.parse(nsMatch[1])] : ["common"];
      for (const m of code.matchAll(/\bt\(\s*"([^"]+)"/g)) {
        const raw = m[1];
        const [ns, key] = raw.includes(":") ? raw.split(":") : [null, raw];
        const candidates = ns ? [ns] : nsList;
        if (!candidates.some((n) => en[n]?.[key] !== undefined)) missing.push(`${file.replace(SRC, "src")}: ${raw}`);
      }
    }
    expect(missing).toEqual([]);
  });

  it("JSX contains no hardcoded user-facing text", () => {
    const offenders: string[] = [];
    for (const file of sources.filter((f) => f.endsWith(".tsx"))) {
      const code = readFileSync(file, "utf8").replace(/\/\/.*$/gm, "");
      // text between a closing ">" of a tag and the next "<" that contains at least one word of 3+ letters
      // text right after an opening JSX tag (<tag ...>) up to the next "<", with a word of 3+ letters
      for (const m of code.matchAll(/<[a-zA-Z][\w.]*(?:\s[^<>]*)?>\s*([^<>{}]*[A-Za-zÄÖÜäöüß]{3,}[^<>{}]*?)\s*</g)) {
        const text = m[1].trim();
        if (BRAND.includes(text)) continue;
        if (/^[\w.]+\s*\(/.test(text) || /=>|&&|\|\||;|\(\)/.test(text)) continue; // TypeScript generics, not JSX text
        offenders.push(`${file.replace(SRC, "src")}: "${text}"`);
      }
    }
    expect(offenders).toEqual([]);
  });

  it("aria-label, title, alt and placeholder props are translated", () => {
    const offenders: string[] = [];
    for (const file of sources.filter((f) => f.endsWith(".tsx"))) {
      const code = readFileSync(file, "utf8");
      for (const m of code.matchAll(/\b(aria-label|title|alt|placeholder)="([^"]*[A-Za-z]{3,}[^"]*)"/g)) {
        if (/^(MotionEngine|https?:\/\/)/.test(m[2])) continue;   // brand name and example URLs
        offenders.push(`${file.replace(SRC, "src")}: ${m[1]}="${m[2]}"`);
      }
    }
    expect(offenders).toEqual([]);
  });
});
