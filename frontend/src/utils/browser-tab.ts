let originalTitle = "";
let titleInterval: number | undefined;

const isBrowser =
  typeof window !== "undefined" && typeof document !== "undefined";

// Use a constant for the notification parameter to avoid hardcoded strings
const NOTIFICATION_PARAM = "notification";

export const browserTab = {
  startNotification(message: string) {
    if (!isBrowser) return;

    // Store original title if not already stored
    if (!originalTitle) {
      originalTitle = document.title;
    }

    // Clear any existing interval
    if (titleInterval) {
      this.stopNotification();
    }

    // Alternate between original title and notification message
    titleInterval = window.setInterval(() => {
      document.title =
        document.title === originalTitle ? message : originalTitle;
    }, 1000);

    // Set favicon to indicate notification
    const favicon = document.querySelector(
      'link[rel="icon"]',
    ) as HTMLLinkElement;
    if (favicon) {
      favicon.href = favicon.href.includes(`?${NOTIFICATION_PARAM}`)
        ? favicon.href
        : `${favicon.href}?${NOTIFICATION_PARAM}`;
    }
  },

  stopNotification() {
    if (!isBrowser) return;

    if (titleInterval) {
      window.clearInterval(titleInterval);
      titleInterval = undefined;
    }
    if (originalTitle) {
      document.title = originalTitle;
    }

    // Reset favicon
    const favicon = document.querySelector(
      'link[rel="icon"]',
    ) as HTMLLinkElement;
    if (favicon) {
      favicon.href = favicon.href.replace(`?${NOTIFICATION_PARAM}`, "");
    }
  },
};
