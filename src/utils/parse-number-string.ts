/**
 * Parses a string as a number, handling commas.
 */
export function parseNumberString(numberString: string | null | undefined) {
  if (!numberString) return null;
  return Number(numberString.replace(/,/g, ""));
}
