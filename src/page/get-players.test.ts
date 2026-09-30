import { GlobalRegistrator } from "@happy-dom/global-registrator";
import { afterAll, beforeAll, expect, test } from "bun:test";
import { loadLineupPage, PAGE_URL } from "../lineup/fixtures/lineup-page";
import { getPlayers } from "./get-players";

beforeAll(() =>
  GlobalRegistrator.register({
    url: PAGE_URL,
    settings: { disableJavaScriptFileLoading: true, disableCSSFileLoading: true, handleDisabledFileLoadingAsSuccess: true },
  }),
);
afterAll(() => GlobalRegistrator.unregister());

// On the saved page, Shaedon Sharpe's recent average shows "15.5↓" (an under-performing arrow)
test("a recent average shown with a trend arrow is read as its number", async () => {
  loadLineupPage();

  const players = await getPlayers();

  expect(players.find((p) => p.playerName === "Shaedon Sharpe")?.last5Avg).toBe(15.5);
});
