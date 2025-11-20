import { chromium, type Page } from "playwright";

if (!process.env.FF_EMAIL || !process.env.FF_PASSWORD) {
  throw new Error("FF_EMAIL and FF_PASSWORD must be set");
}

(async () => {
  await build();

  async function runScript(page: Page): Promise<void> {
    const url =
      "https://www.fleaflicker.com/nba/leagues/30579/teams/161025?statType=0";

    console.log(`Navigating to ${url}...`);
    await page.goto(url);

    console.log("Adding script tag...");
    await page.waitForLoadState("load");

    await login(page);

    await page.waitForTimeout(2000);
    console.log("Running pageLoad...");
    await page.addScriptTag({
      path: "./extension/dist/page-load__set-lineup.js",
    });
    console.log("pageLoad complete");

    await page.waitForTimeout(2000);
    console.log("Running main...");
    await page.addScriptTag({
      path: "./extension/dist/main.js",
    });

    await page.waitForTimeout(1000000);
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

async function login(page: Page) {
  const loginInitButton = page.getByText("Log In");
  console.log("Login button:", loginInitButton);
  const isLoggedIn = !(await loginInitButton.isVisible());
  if (isLoggedIn) {
    console.log("Already logged in");
    return;
  }

  console.log("Logging in...");
  await loginInitButton.click();

  const emailInput = page.getByRole("textbox", { name: "email" });
  const passwordInput = page.getByRole("textbox", { name: "password" });
  const loginButton = page.getByRole("button", { name: "Log In" });

  console.log("Waiting for email input...");
  await page.waitForSelector('input[name="email"]');
  console.log("Email input HTML:", await emailInput.evaluate((node) => node.outerHTML));

  await emailInput.fill(process.env.FF_EMAIL ?? "");
  await passwordInput.fill(process.env.FF_PASSWORD ?? "");
  await loginButton.click();

  await page.waitForTimeout(1000000);
}

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
