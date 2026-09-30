/**
 * Parses a string as a number, handling commas and trailing text such as a trend arrow ("15.5↓")
 */
export function parseNumberString(numberString: string | null | undefined) {
  if (!numberString) return null;
  return parseFloat(numberString.replace(/,/g, ""));
}
