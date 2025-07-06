import { CSSProperties } from "react";
import toast, { ToastOptions } from "react-hot-toast";

const TOAST_STYLE: CSSProperties = {
  background: "#454545",
  border: "1px solid #717888",
  color: "#fff",
  borderRadius: "4px",
};

const TOAST_OPTIONS: ToastOptions = {
  position: "top-right",
  style: TOAST_STYLE,
};

/**
 * Calculate toast duration based on message length
 * @param message - The message to display
 * @param minDuration - Minimum duration in milliseconds (default: 5000 for success, 4000 for error)
 * @param maxDuration - Maximum duration in milliseconds (default: 10000)
 * @returns Duration in milliseconds
 */
const calculateToastDuration = (
  message: string,
  minDuration: number = 5000,
  maxDuration: number = 10000,
): number => {
  // Calculate duration based on reading speed (average 200 words per minute)
  // Assuming average word length of 5 characters
  const wordsPerMinute = 200;
  const charactersPerMinute = wordsPerMinute * 5;
  const charactersPerSecond = charactersPerMinute / 60;

  // Calculate time needed to read the message
  const readingTimeMs = (message.length / charactersPerSecond) * 1000;

  // Add some buffer time (50% extra) for processing
  const durationWithBuffer = readingTimeMs * 1.5;

  // Ensure duration is within min/max bounds
  return Math.min(Math.max(durationWithBuffer, minDuration), maxDuration);
};

export const displayErrorToast = (error: string) => {
  const duration = calculateToastDuration(error, 4000);
  toast.error(error, { ...TOAST_OPTIONS, duration });
};

export const displaySuccessToast = (message: string) => {
  const duration = calculateToastDuration(message, 5000);
  toast.success(message, { ...TOAST_OPTIONS, duration });
};
