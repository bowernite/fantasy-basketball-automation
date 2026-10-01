const MAX_NEWS_AGE_MS = 36 * 60 * 60 * 1000;
const LEAGUE_DAY_START_HOUR_ET = 6;

const DAY_REF = String.raw`\b(?:(?:Mon|Tues|Wednes|Thurs|Fri|Satur|Sun)day|tonight|today|tomorrow|yesterday|last night)\b`;
// Up to two words between, e.g. "hasn't been", "has not yet been"
const NOT_NEGATED = String.raw`(?<!(?:\bnot|n['’]t|\bnever|\bno longer)(?:\s+\w+){0,2}\s+)`;
const OUT_PHRASE = new RegExp(String.raw`${NOT_NEGATED}(?:\bruled out\b|\bwill not play\b|\bwon['’]t play\b|\bout\s+${DAY_REF})`, "i");

export type OutNewsMatch = { status: "OUT" | "D"; sentence: string };

/** The sentence in a news item saying the player is OUT or D for the game tipping at `tipAt`, read strictly */
export function matchOutNews(news: { headline: string; body: string; postedAt: string }, tipAt: string): OutNewsMatch | undefined {
  const newsAgeAtTip = Date.parse(tipAt) - Date.parse(news.postedAt);
  if (!(newsAgeAtTip > 0 && newsAgeAtTip <= MAX_NEWS_AGE_MS)) return undefined;
  const namesTipDay = tipDayRefMatcher(news.postedAt, tipAt);
  for (const sentence of [news.headline, ...splitSentences(news.body)]) {
    const dayRefs = sentence.match(new RegExp(DAY_REF, "gi")) ?? [];
    const namesOnlyTipDay = dayRefs.length > 0 && dayRefs.every(namesTipDay);
    if (namesOnlyTipDay && OUT_PHRASE.test(sentence)) return { status: "OUT", sentence };
  }
  return undefined;
}

function tipDayRefMatcher(postedAt: string, tipAt: string) {
  const tip = easternDay(tipAt);
  const posted = easternDay(postedAt);
  const postedOnTipDay = posted.date === tip.date && posted.hour >= LEAGUE_DAY_START_HOUR_ET;
  return (dayRef: string) => {
    const ref = dayRef.toLowerCase();
    if (ref === "tonight" || ref === "today") return postedOnTipDay;
    return ref === tip.weekday.toLowerCase();
  };
}

function splitSentences(text: string) {
  return text.split(/(?<=[.!?])\s+/);
}

function easternDay(iso: string) {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: "America/New_York",
    hourCycle: "h23",
    weekday: "long",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "numeric",
  }).formatToParts(new Date(iso));
  const part = (type: Intl.DateTimeFormatPartTypes) => parts.find((p) => p.type === type)?.value ?? "";
  return { date: `${part("year")}-${part("month")}-${part("day")}`, weekday: part("weekday"), hour: Number(part("hour")) };
}
