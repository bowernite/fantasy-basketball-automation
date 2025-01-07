import { chromium, type Page } from "playwright";

(async () => {
  await build();

  async function runScript(page: Page): Promise<void> {
    const url =
      "https://www.fleaflicker.com/nba/leagues/30579/teams/161025?statType=0";

    console.log(`Navigating to ${url}...`);
    await page.goto(url);

    console.log("Adding script tag...");
    await page.waitForLoadState("load");

    await page.waitForTimeout(2000);
    console.log("Running pageLoad...");
    await page.addScriptTag({
      path: "./chrome-extension/dist/page-load__set-lineup.js",
    });
    console.log("pageLoad complete");

    await page.waitForTimeout(2000);
    console.log("Running main...");
    await page.addScriptTag({
      path: "./chrome-extension/dist/main.js",
    });
  }

  const browser = await chromium.launch({
    // headless: process.env.HEADLESS !== "false", // Toggle headless via environment variable
    headless: false,
    // slowMo: 500,
  });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    await runScript(page);
  } catch (err) {
    console.error("Error running script:", err);
  } finally {
    await browser.close();
  }
})();

async function build(): Promise<void> {
  const { exec } = require("child_process");

  return new Promise((resolve, reject) => {
    exec(
      "./build.sh --no-browser",
      (error: Error | null, stdout: string, stderr: string) => {
        if (error) {
          console.error(`Error executing build.sh: ${error}`);
          reject(error);
          return;
        }

        if (stderr) {
          console.error(`Build script stderr: ${stderr}`);
        }

        console.log(stdout);
        resolve();
      }
    );
  });
}
