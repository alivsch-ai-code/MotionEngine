// End-to-end check of the web app against a running MotionEngine service (default http://127.0.0.1:8000).
//   node e2e/run.mjs [--screens]     BASE_URL=... to point elsewhere
// Visits every page in English and German, dark and light; runs the main workflows; fails on console
// errors, untranslated keys or missing landmarks. --screens writes screenshots to e2e/output/.
import { mkdirSync } from "node:fs";
import { createRequire } from "node:module";

// playwright from the project (CI) or from the global installation (NODE_PATH)
async function loadPlaywright() {
  try {
    return await import("playwright");
  } catch {
    const roots = (process.env.NODE_PATH ?? "").split(":").filter(Boolean);
    return createRequire(import.meta.url)(require_resolve(roots));
  }
}
function require_resolve(roots) {
  for (const r of roots) { try { return createRequire(r + "/")?.resolve("playwright"); } catch { /* next */ } }
  return "playwright";
}
const { chromium } = await loadPlaywright();

const BASE = process.env.BASE_URL ?? "http://127.0.0.1:8000";
const SCREENS = process.argv.includes("--screens");
const OUT = new URL("./output/", import.meta.url).pathname;
if (SCREENS) mkdirSync(OUT, { recursive: true });

const PAGES = ["/", "/app", "/app/assistant", "/app/simulate", "/app/trajectory", "/app/inspector", "/app/parking", "/app/workbench", "/app/research", "/app/architecture", "/app/matlab", "/app/knowledge", "/app/predict", "/app/vehicles", "/app/models", "/app/settings", "/app/design", "/app/does-not-exist"];
// raw i18n keys look like "simulate.title" or "app:models.x": letters, dots, no spaces
const RAW_KEY = /(^|\s)(common|app|domain|inspector|landing):[a-z]|(^|\s)[a-z]+(\.[a-zA-Z_]+){2,}(\s|$)/;
const failures = [];
const timings = {};

const browser = await chromium.launch();
async function newPage(lang, theme) {
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, locale: lang, colorScheme: theme, deviceScaleFactor: SCREENS ? 1 : 1 });
  await ctx.addInitScript(([l, th]) => { try { localStorage.setItem("me.lang", l); localStorage.setItem("me.theme", th); } catch {} }, [lang, theme]);
  const page = await ctx.newPage();
  page.on("console", (m) => { if (m.type() === "error") failures.push(`[${lang}/${theme}] console: ${m.text()}`); });
  page.on("pageerror", (e) => failures.push(`[${lang}/${theme}] pageerror: ${e.message}`));
  return page;
}
async function checkText(page, label) {
  const text = await page.locator("body").innerText();
  const raw = text.split("\n").filter((line) => RAW_KEY.test(line.trim()) && !/\/|https?:|vdsim|motion-engine|MOTIONENGINE|\.json|\.md|\.onnx|neural_/.test(line));
  if (raw.length) failures.push(`${label}: untranslated keys? ${raw.slice(0, 3).join(" | ")}`);
}

for (const [lang, theme] of [["en", "dark"], ["de", "light"], ["de", "dark"], ["en", "light"]]) {
  const page = await newPage(lang, theme);
  for (const path of PAGES) {
    const t0 = Date.now();
    await page.goto(BASE + path, { waitUntil: "networkidle" });
    timings[`${lang}/${theme} ${path}`] = Date.now() - t0;
    if ((await page.locator("h1").count()) === 0) failures.push(`${lang} ${path}: no h1`);
    if (path.startsWith("/app") && (await page.locator("nav[aria-label]").count()) === 0) failures.push(`${lang} ${path}: no navigation landmark`);
    const htmlLang = await page.evaluate(() => document.documentElement.lang);
    if (htmlLang !== lang) failures.push(`${path}: html lang ${htmlLang} != ${lang}`);
    await checkText(page, `${lang} ${path}`);
    if (SCREENS && (lang === "en" || path !== "/")) {
      await page.screenshot({ path: `${OUT}${(path.replace(/\//g, "_") || "_root").replace(/^_/, "") || "landing"}-${lang}-${theme}.png` });
    }
  }
  await page.context().close();
}

// workflows (English, dark): simulation, inspector steps, prediction, training
const page = await newPage("en", "dark");
let t0 = Date.now();
await page.goto(BASE + "/app/simulate", { waitUntil: "networkidle" });
await page.getByRole("button", { name: "Run simulation" }).click();
await page.getByText("Driven path").waitFor({ timeout: 60000 });
await page.locator(".chart canvas").first().waitFor({ timeout: 20000 });
timings["workflow simulate"] = Date.now() - t0;
await checkText(page, "simulate result");
if (SCREENS) await page.screenshot({ path: `${OUT}simulate-result-en-dark.png`, fullPage: true });

t0 = Date.now();
await page.goto(BASE + "/app/inspector", { waitUntil: "networkidle" });
await page.getByRole("button", { name: "Lane change at 20 m/s" }).click();
await page.getByText("Candidate set and selected trajectory").waitFor({ timeout: 30000 });
await page.locator(".katex").first().waitFor({ timeout: 20000 });
timings["workflow inspector"] = Date.now() - t0;
for (const step of ["Start state", "Lateral motion: quintic polynomial", "Longitudinal motion", "Combination and selection", "Frenet to world coordinates", "Restrictions", "Vehicle physics"]) {
  await page.getByRole("button", { name: step }).click();
  await page.locator("#step-title", { hasText: step }).waitFor();
  await page.locator(".katex").first().waitFor();
  await checkText(page, `inspector ${step}`);
  if (step.startsWith("Lateral") || step.startsWith("Longitudinal")) {
    if ((await page.getByText(/Verified: the coefficients/).count()) === 0) failures.push(`inspector ${step}: verification banner missing`);
  }
  if (SCREENS && step.startsWith("Lateral")) await page.screenshot({ path: `${OUT}inspector-lateral-en-dark.png`, fullPage: true });
}

await page.goto(BASE + "/app/predict", { waitUntil: "networkidle" });
await page.getByRole("button", { name: "Predict", exact: true }).first().click();
await page.getByText("Predicted paths").waitFor({ timeout: 20000 });

t0 = Date.now();
await page.goto(BASE + "/app/models", { waitUntil: "networkidle" });
await page.getByRole("tab", { name: "Train" }).click();
await page.getByLabel("Training samples").fill("4000");
await page.getByText("Expert settings").click();
await page.getByLabel("Epochs").fill("40");
await page.getByRole("button", { name: "Start training" }).click();
await page.locator("tr", { hasText: "MotionEngine MLP" }).first().waitFor({ timeout: 90000 });
timings["workflow training"] = Date.now() - t0;
await page.getByRole("button", { name: "Compare with physics" }).click();
await page.getByText("Max. position difference").waitFor({ timeout: 60000 });
await checkText(page, "models");
if (SCREENS) await page.screenshot({ path: `${OUT}models-evaluated-en-dark.png`, fullPage: true });

// live mode of the workbench: steps, then keep the result as a run
t0 = Date.now();
await page.goto(BASE + "/app/workbench", { waitUntil: "networkidle" });
await page.getByRole("button", { name: "Live", exact: true }).click();
await page.locator(".player__view").waitFor({ timeout: 30000 });
await page.getByRole("button", { name: "10 steps" }).click();
await page.getByRole("button", { name: "Keep as run" }).click();
await page.locator(".tabs").waitFor({ timeout: 30000 });
timings["workflow live"] = Date.now() - t0;
await checkText(page, "workbench live");

// trajectory editor: drive the drawn path, then the run comparison lists it
await page.goto(BASE + "/app/trajectory", { waitUntil: "networkidle" });
await page.locator(".editor__handle").first().waitFor();
await page.getByText(/^Length /).waitFor({ timeout: 20000 });
await page.getByRole("button", { name: "Drive this trajectory" }).click();
await page.getByText(/Trajectory from the editor/).waitFor();
await page.getByRole("button", { name: "Run simulation" }).click();
await page.getByText(/Run comparison and report/).waitFor({ timeout: 60000 });
if ((await page.getByText(/Editor path/).count()) === 0) failures.push("editor run: not listed in the run comparison");
await checkText(page, "editor run");
await page.getByRole("button", { name: "Remove", exact: true }).click();

// trajectory planner model: train on a few demonstrations, then drive against the teacher
t0 = Date.now();
await page.goto(BASE + "/app/models", { waitUntil: "networkidle" });
await page.getByRole("tab", { name: "Train" }).click();
await page.getByLabel("What to train").selectOption("trajectory_planner");
await page.getByLabel("Demonstrations").fill("500");
await page.getByText("Expert settings").click();
await page.getByLabel("Epochs").fill("40");
await page.getByRole("button", { name: "Start training" }).click();
await page.getByText("Cycles solved by the network").first().waitFor({ timeout: 180000 });
timings["workflow planner training"] = Date.now() - t0;
await page.getByRole("button", { name: "Slower vehicle ahead" }).click();
await page.getByText("Largest path difference").waitFor({ timeout: 60000 });
await checkText(page, "planner model");

// German workflow labels
const de = await newPage("de", "dark");
await de.goto(BASE + "/app/inspector", { waitUntil: "networkidle" });
await de.getByRole("button", { name: "Kurve R = 120 m" }).click();
await de.getByText("Kandidatenmenge und gewählte Trajektorie").waitFor({ timeout: 30000 });
await de.getByRole("button", { name: "Querbewegung: Polynom 5. Grades" }).click();
await de.locator(".katex").first().waitFor();
await checkText(de, "de inspector");
if (SCREENS) await de.screenshot({ path: `${OUT}inspector-lateral-de-dark.png`, fullPage: true });

// mobile layout: navigation behind the menu button, no horizontal overflow
const mobile = await browser.newPage({ viewport: { width: 390, height: 844 } });
await mobile.goto(BASE + "/app/simulate", { waitUntil: "networkidle" });
const overflow = await mobile.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
if (overflow > 1) failures.push(`mobile: horizontal overflow ${overflow}px`);
await mobile.getByRole("button", { name: "Open navigation" }).click();
await mobile.getByRole("link", { name: "Trajectory inspector" }).click();
await mobile.locator("h1", { hasText: "Trajectory inspector" }).waitFor();
if (SCREENS) await mobile.screenshot({ path: `${OUT}mobile-inspector-en.png` });

await browser.close();
console.log(JSON.stringify({ timings_ms: timings }, null, 1));
if (failures.length) {
  console.error("FAILURES:\n" + failures.join("\n"));
  process.exit(1);
}
console.log("e2e: all checks passed");
