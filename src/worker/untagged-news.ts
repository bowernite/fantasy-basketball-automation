import { parseHTML } from "linkedom";
import { parsePlayerNews } from "../page/player-status";

const FRESH_NEWS_MS = 36 * 60 * 60 * 1000;

/** `status`: OUT or D when the news loosely reads so and is under 36 h old */
export type UntaggedNews = { player: string; status?: "OUT" | "D"; postedAt: string; headline: string; body: string };

/** News on players with no injury tag on a team page */
export function findUntaggedNews(html: string): UntaggedNews[] {
  const { document } = parseHTML(html);
  const tooltips = readTooltips(document);
  return Array.from(document.querySelectorAll("tr")).flatMap((row) => {
    const newsIcon = row.querySelector(".fa-file-text-o, .fa-file-text");
    const newsHtml = newsIcon && tooltips.get(newsIcon.id);
    if (!newsHtml || row.querySelector(".injury")) return [];
    const news = parseHTML(`<div>${newsHtml}</div>`).document;
    const postedAt = news.querySelector("relative-time")?.getAttribute("datetime");
    if (postedAt == null) return [];
    const looseStatus = parsePlayerNews(news.documentElement.textContent ?? "", undefined)?.injuryStatus;
    const fresh = Date.now() - Date.parse(postedAt) <= FRESH_NEWS_MS;
    const status = fresh && (looseStatus === "OUT" || looseStatus === "D") ? looseStatus : undefined;
    const [headline, body] = ["h5", "p"].map((selector) => news.querySelector(selector)?.textContent ?? "");
    return [{ player: row.querySelector(".player-text")?.textContent ?? "", ...(status && { status }), postedAt, headline, body }];
  });
}

function readTooltips(document: Document) {
  const pageData = document.getElementById("page-data")?.textContent?.match(/window\.pageData\s*=\s*(\{.*?\});/s)?.[1];
  const tooltips: { ids: string[]; contents: string }[] = pageData ? (JSON.parse(pageData).tooltips ?? []) : [];
  return new Map(tooltips.flatMap(({ ids, contents }) => ids.map((id) => [id, contents] as const)));
}
