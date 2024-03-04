/**
 * Determine color for each sentence based on sentimen score
 */
export function calculateColor(score: number, label: string): string {
  switch (label) {
    case "positive":
      return "#4caf50";
    case "negative":
      return "#ef5350";
    default:
      return "#ff9800";
  }
}
