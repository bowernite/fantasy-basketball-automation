/**
 * Interpolates between two colors based on a percentage.
 * e.g. given yellow and green, a lower percentage will be closer to yellow,
 * and a higher percentage will be closer to green.
 *
 * @param color1 - The first color in the format "rgb(r1, g1, b1)".
 * @param color2 - The second color in the format "rgb(r2, g2, b2)".
 * @param percentage - A number between 0 and 1 representing the interpolation percentage.
 * @returns The interpolated color in the format "rgb(r, g, b)".
 */
export function interpolateColors(
  color1: string,
  color2: string,
  percentage: number
) {
  const rgb1 = color1.match(/\d+/g)!.map(Number);
  const rgb2 = color2.match(/\d+/g)!.map(Number);

  const interpolatedColor = rgb1.map((channel1, i) => {
    const channel2 = rgb2[i];
    return Math.round(channel1 + (channel2 - channel1) * percentage);
  });

  return `rgb(${interpolatedColor.join(", ")})`;
}
