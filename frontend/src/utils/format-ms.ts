/**
 * Formats a time in milliseconds to the format "mm:ss"
 * @param ms The time in milliseconds
 * @returns The formatted time in the format "mm:ss"
 *
 * @example
 * formatMs(1000) // "00:01"
 * formatMs(1000 * 60) // "01:00"
 * formatMs(1000 * 60 * 2.5) // "02:30"
 */
export const formatMs = (ms: number) => {
  const minutes = Math.floor(ms / 1000 / 60);
  const seconds = Math.floor((ms / 1000) % 60);

  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
};
