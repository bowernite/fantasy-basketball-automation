/**
 * Interpolates between two colors based on a percentage, with optional color stops in between.
 * e.g. given start and end colors, a lower percentage will be closer to the start,
 * and a higher percentage will be closer to the end.
 * Additional color stops can be defined at specific percentages between 0 and 1.
 *
 * @param colors - Object containing the colors in "rgb(r, g, b)" format
 * @param colors.start - The starting color
 * @param colors.end - The ending color
 * @param colors.stops - Optional array of color stops with percentage and color
 * @param percentage - A number between 0 and 1 representing the interpolation percentage
 * @returns The interpolated color in the format "rgb(r, g, b)"
 */
export function interpolateColors(
  colors: {
    start: string;
    end: string;
    stops?: Array<{
      color: string;
      percentage: number;
    }>;
  },
  percentage: number
) {
  const rgbStart = colors.start.match(/\d+/g)!.map(Number);
  const rgbEnd = colors.end.match(/\d+/g)!.map(Number);

  if (!colors.stops?.length) {
    const interpolatedColor = rgbStart.map((channelStart, i) => {
      const channelEnd = rgbEnd[i];
      return Math.round(
        channelStart + (channelEnd - channelStart) * percentage
      );
    });
    return `rgb(${interpolatedColor.join(", ")})`;
  }

  const sortedStops = [...colors.stops].sort(
    (a, b) => a.percentage - b.percentage
  );

  // Find the two colors to interpolate between based on percentage
  let startColor = rgbStart;
  let endColor = rgbEnd;
  let startPercentage = 0;
  let endPercentage = 1;

  for (let i = 0; i < sortedStops.length; i++) {
    const stop = sortedStops[i];
    if (percentage <= stop.percentage) {
      endColor = stop.color.match(/\d+/g)!.map(Number);
      endPercentage = stop.percentage;
      break;
    }
    startColor = stop.color.match(/\d+/g)!.map(Number);
    startPercentage = stop.percentage;
  }

  // Adjust percentage to be relative to the two colors we're interpolating between
  const adjustedPercentage =
    (percentage - startPercentage) / (endPercentage - startPercentage);

  const interpolatedColor = startColor.map((channelStart, i) => {
    const channelEnd = endColor[i];
    return Math.round(
      channelStart + (channelEnd - channelStart) * adjustedPercentage
    );
  });
  return `rgb(${interpolatedColor.join(", ")})`;
}
