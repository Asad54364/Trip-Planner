/**
 * Convert an hour value (0-24) to an x-coordinate on the SVG grid.
 * Shared between the grid, duty lines, and bracket layers.
 */
export function hourToX(hour: number, gridLeft: number, gridWidth: number): number {
  return gridLeft + (hour / 24) * gridWidth
}

/**
 * Map a duty status to its row index (0-based from top).
 */
export function statusToRow(status: string): number {
  switch (status) {
    case 'OFF_DUTY': return 0
    case 'SLEEPER_BERTH': return 1
    case 'DRIVING': return 2
    case 'ON_DUTY_NOT_DRIVING': return 3
    default: return 0
  }
}

/**
 * Format hours as HH:MM string.
 */
export function formatHours(hours: number): string {
  const h = Math.floor(hours)
  const m = Math.round((hours - h) * 60)
  return `${h}:${m.toString().padStart(2, '0')}`
}
