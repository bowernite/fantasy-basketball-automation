import { getPageDate } from "../page/page-querying";

export function getNumDaysInFuture() {
  const pageDate = getPageDate();
  const today = new Date(new Date().setHours(0, 0, 0, 0));
  const diffInMs = pageDate.getTime() - today.getTime();
  const diffInDays = Math.floor(diffInMs / (1000 * 60 * 60 * 24));
  return diffInDays;
}

/**
 * Parses a date string like "1/2" or "12/30/25" into its components.
 * Returns null if the string doesn't match the expected format.
 */
export function parseDateText(dateText: string): {
  month: number;
  day: number;
  yearSuffix: number | null;
} | null {
  const dateMatch = dateText.match(/(\d{1,2})\/(\d{1,2})(?:\/(\d{2}))?/);
  if (!dateMatch) {
    return null;
  }
  
  return {
    month: Number(dateMatch[1]),
    day: Number(dateMatch[2]),
    yearSuffix: dateMatch[3] ? Number(dateMatch[3]) : null,
  };
}

/**
 * Converts a 2-digit year suffix (like 25) to a full year (like 2025)
 * by using the current century.
 */
export function parseYearFromSuffix(
  yearSuffix: number,
  currentYear: number
): number {
  const century = Math.floor(currentYear / 100) * 100;
  return century + yearSuffix;
}

/**
 * Determines the correct year for a date when no year is specified.
 * Uses a "closest to reference date" heuristic by comparing the date in
 * the current year, next year, and previous year, returning whichever
 * produces a date closest to the reference date.
 * 
 * This handles year boundary transitions (e.g., viewing Jan 2 from late December).
 */
export function findClosestYearForDate(
  month: number,
  day: number,
  referenceDate: Date = new Date()
): number {
  const currentYear = referenceDate.getFullYear();
  
  const candidateThisYear = new Date(currentYear, month - 1, day);
  const candidateNextYear = new Date(currentYear + 1, month - 1, day);
  const candidatePrevYear = new Date(currentYear - 1, month - 1, day);
  
  const diffThis = Math.abs(candidateThisYear.getTime() - referenceDate.getTime());
  const diffNext = Math.abs(candidateNextYear.getTime() - referenceDate.getTime());
  const diffPrev = Math.abs(candidatePrevYear.getTime() - referenceDate.getTime());
  
  if (diffThis <= diffNext && diffThis <= diffPrev) {
    return currentYear;
  } else if (diffNext <= diffPrev) {
    return currentYear + 1;
  } else {
    return currentYear - 1;
  }
}

/**
 * Converts a date string (like "1/2" or "12/30/25") into a Date object.
 * If a year suffix is provided, it's used directly. Otherwise, the year is
 * determined using the "closest to reference date" heuristic.
 * Returns null if the date string can't be parsed.
 */
export function parseDateFromText(
  dateText: string,
  referenceDate: Date = new Date()
): Date | null {
  const parsed = parseDateText(dateText);
  if (!parsed) {
    return null;
  }
  
  const { month, day, yearSuffix } = parsed;
  const currentYear = referenceDate.getFullYear();
  
  const year = yearSuffix !== null
    ? parseYearFromSuffix(yearSuffix, currentYear)
    : findClosestYearForDate(month, day, referenceDate);
  
  return new Date(year, month - 1, day);
}

