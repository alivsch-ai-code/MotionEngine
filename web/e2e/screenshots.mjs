// Product screenshots for the landing page and the documentation (1440 x 900 viewport).
//   node e2e/screenshots.mjs    -> web/public/screenshots/{inspector,simulate}-{dark,light}.png
import { mkdirSync } from "node:fs";
import { createRequire } from "node:module";

const BASE = process.env.BASE_URL ?? "http://127.0.0.1:8000";
const OUT = new URL("../public/screenshots/", import.meta.url).pathname;
mkdirSync(OUT, { recursive: true });
let pw;
try { pw = await import("playwright"); } catch { pw = createRequire((process.env.NODE_PATH ?? "") + "/")("playwright"); }
const browser = await pw.chromium.launch();
for (const theme of ["dark", "light"]) {
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, colorScheme: theme });
  await ctx.addInitScript((th) => { localStorage.setItem("me.lang", "en"); localStorage.setItem("me.theme", th); }, theme);
  const page = await ctx.newPage();
  await page.goto(`${BASE}/app/inspector`, { waitUntil: "networkidle" });
  await page.getByRole("button", { name: "Lane change at 20 m/s" }).click();
  await page.getByRole("button", { name: "Lateral motion: quintic polynomial" }).click();
  await page.locator(".katex").first().waitFor();
  await page.locator(".chart canvas").first().waitFor();
  await page.locator("#step-title").scrollIntoViewIfNeeded();
  await page.evaluate(() => document.querySelector(".shell__main")?.scrollTo(0, 260));
  await page.screenshot({ path: `${OUT}inspector-${theme}.png` });
  await page.goto(`${BASE}/app/simulate`, { waitUntil: "networkidle" });
  await page.getByRole("button", { name: "Run simulation" }).click();
  await page.locator(".chart canvas").first().waitFor({ timeout: 60000 });
  await page.waitForTimeout(300);
  await page.screenshot({ path: `${OUT}simulate-${theme}.png` });
  await ctx.close();
}
await browser.close();
console.log("screenshots written to", OUT);
