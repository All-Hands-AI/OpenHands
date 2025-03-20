/* eslint-disable no-console */

/**
 * A utility class for logging events. This class will log events in development mode
 * and can be forced to log in any environment by setting FORCE_LOGGING to true.
 */
class EventLogger {
  static isDevMode = process.env.NODE_ENV === "development";

  static FORCE_LOGGING = false; // Set to false for production, true only for debugging

  static shouldLog() {
    return this.isDevMode || this.FORCE_LOGGING;
  }

  /**
   * Format and log a message event
   * @param event The raw event object
   */
  static message(event: MessageEvent) {
    if (this.shouldLog()) {
      console.warn(
        "[OpenHands]",
        JSON.stringify(JSON.parse(event.data.toString()), null, 2),
      );
    }
  }

  /**
   * Log an event with a name
   * @param event The raw event object
   * @param name The name of the event
   */
  static event(event: Event, name?: string) {
    if (this.shouldLog()) {
      console.warn("[OpenHands]", name || "EVENT", event);
    }
  }

  /**
   * Log a warning message
   * @param warning The warning message
   */
  static warning(warning: string) {
    if (this.shouldLog()) {
      console.warn("[OpenHands]", warning);
    }
  }

  /**
   * Log an info message
   * @param info The info message
   */
  static info(info: string) {
    if (this.shouldLog()) {
      console.info("[OpenHands]", info);
    }
  }

  /**
   * Log an error message
   * @param error The error message
   */
  static error(error: string) {
    if (this.shouldLog()) {
      console.error("[OpenHands]", error);
    }
  }
}

export default EventLogger;
