const MAX_NEWS_AGE_MS = 36 * 60 * 60 * 1000;
const LEAGUE_DAY_START_HOUR_ET = 6;

const MONTH = String.raw`(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)`;
const MONTH_DAY = String.raw`\b${MONTH}\.?\s+\d{1,2}(?:st|nd|rd|th)?\b|(?<![\d/])\d{1,2}\/\d{1,2}(?!\d)`;
const DAY_REF = String.raw`\b(?:Mon(?:day)?|Tue(?:s(?:day)?)?|Wed(?:nesday)?|Thu(?:r(?:s(?:day)?)?)?|Fri(?:day)?|Sat(?:urday)?|Sun(?:day)?|tonight|today|tomorrow|yesterday|last night)\b|${MONTH_DAY}`;
// Up to two words between, e.g. "hasn't been", "has not yet been"
const NOT_NEGATED = String.raw`(?<!(?:\bnot|n['’]t|\bnever|\bno longer)(?:\s+\w+){0,2}\s+)`;
const MONTH_ABBREVIATIONS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"];
const NOT_IDIOM = String.raw`(?<!\b(?:sat|sit|sits|sitting|fouled|fouls|closed|closes|closing|moved|moves|played|plays|worked|works|checked|came|comes|went|goes|stepped|steps|turned|turns|cashed)\s+)`;
const OUT_PHRASE = new RegExp(String.raw`${NOT_NEGATED}(?:\bruled out\b|\bwill not play\b|\bwon['’]t play\b|${NOT_IDIOM}\bout\s+(?:(?:for|against)(?:\s+\S+){0,4}\s+)?${DAY_REF})`, "i");
const DOUBTFUL_PHRASE = new RegExp(String.raw`${NOT_NEGATED}\bdoubtful\b`, "i");
const HEDGE = /\b(?:could|might|may|would|should|if|unless|possibly|likely|questionable|probable|upgraded)\b/i;
// Phrasing for a teammate being out, mentioned in the player's news
const TEAMMATE_CONTEXT = /^With\b|\b(?:who|absence|in place of|usage|minutes|start|starts|starting)\b/i;

export type OutNewsMatch = { status: "OUT" | "D"; sentence: string };

/** The sentence in a news item saying the player is OUT or D for the game tipping at `tipAt`, read strictly */
export function matchOutNews(news: { headline: string; body: string; postedAt: string }, tipAt: string): OutNewsMatch | undefined {
  const newsAgeAtTip = Date.parse(tipAt) - Date.parse(news.postedAt);
  if (!(newsAgeAtTip > 0 && newsAgeAtTip <= MAX_NEWS_AGE_MS)) return undefined;
  const namesTipDay = tipDayRefMatcher(news.postedAt, tipAt);
  for (const sentence of [news.headline, ...splitSentences(news.body)]) {
    const dayRefs = sentence.match(new RegExp(DAY_REF, "gi")) ?? [];
    const namesOnlyTipDay = dayRefs.length > 0 && dayRefs.every(namesTipDay);
    if (!namesOnlyTipDay || HEDGE.test(sentence) || TEAMMATE_CONTEXT.test(sentence)) continue;
    if (OUT_PHRASE.test(sentence)) return { status: "OUT", sentence };
    if (DOUBTFUL_PHRASE.test(sentence)) return { status: "D", sentence };
  }
  return undefined;
}

function tipDayRefMatcher(postedAt: string, tipAt: string) {
  const tip = easternDay(tipAt);
  const posted = easternDay(postedAt);
  const postedInLeagueDay = posted.hour >= LEAGUE_DAY_START_HOUR_ET;
  const postedOnTipDay = postedInLeagueDay && posted.date === tip.date;
  const postedDayBeforeTip = postedInLeagueDay && posted.date === dayBefore(tip.date);
  return (dayRef: string) => {
    const ref = dayRef.toLowerCase();
    if (ref === "tonight" || ref === "today") return postedOnTipDay;
    if (ref === "tomorrow") return postedDayBeforeTip;
    const monthDay = parseMonthDay(dayRef);
    if (monthDay) return monthDay.month === tip.month && monthDay.day === tip.day;
    return ref.slice(0, 3) === tip.weekday.slice(0, 3).toLowerCase();
  };
}

function dayBefore(date: string) {
  return new Date(Date.parse(date) - 24 * 60 * 60 * 1000).toISOString().slice(0, 10);
}

function parseMonthDay(dayRef: string) {
  const numeric = dayRef.match(/^(\d{1,2})\/(\d{1,2})$/);
  if (numeric) return { month: Number(numeric[1]), day: Number(numeric[2]) };
  const named = dayRef.match(/^([a-z]{3})\D*(\d{1,2})/i);
  if (!named) return undefined;
  const month = MONTH_ABBREVIATIONS.indexOf(named[1].toLowerCase()) + 1;
  return { month, day: Number(named[2]) };
}

function splitSentences(text: string) {
  const sentences = text.trim().split(/(?<!\b(?:Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec|vs|Jr|Sr|St|Mr|Dr|No|[A-Z])\.)(?<=[.!?])\s+(?=[A-Z"“'‘])/);
  const truncated = /(?:\.\.\.|…)$/.test(sentences.at(-1) ?? "");
  return truncated ? sentences.slice(0, -1) : sentences;
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
  return {
    date: `${part("year")}-${part("month")}-${part("day")}`,
    month: Number(part("month")),
    day: Number(part("day")),
    weekday: part("weekday"),
    hour: Number(part("hour")),
  };
}
