import { chromium, type Page } from "playwright";

(async () => {
  async function runScript(page: Page): Promise<void> {
    await page.addInitScript({
      path: "./chrome-extension/dist/page-load__set-lineup.js",
    });
    const url =
      "https://www.fleaflicker.com/nba/leagues/30579/teams/161025?statType=0"; // Replace with your URL
    console.log(`Navigating to ${url}...`);
    await page.goto(url);

    console.log("Adding script tag...");
    await page.addScriptTag({
      path: "./chrome-extension/dist/page-load__set-lineup.js",
    });

    // Your script logic here
    console.log("Script logic executed");

    console.log("Waiting for 5 seconds...");
    await page.waitForTimeout(5000);
    console.log("Running pageLoad...");
    await page.evaluate(() => {
      // @ts-ignore
      pageLoad();
    });
    console.log("pageLoad complete");
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
