let originalTitle = document.title;
let titleInterval: number | undefined;

export const browserTab = {
  startNotification(message: string) {
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
      document.title = document.title === originalTitle ? message : originalTitle;
    }, 1000);

    // Set favicon to indicate notification
    const favicon = document.querySelector('link[rel="icon"]') as HTMLLinkElement;
    if (favicon) {
      favicon.href = favicon.href.includes("?notification")
        ? favicon.href
        : `${favicon.href}?notification`;
    }
  },

  stopNotification() {
    if (titleInterval) {
      window.clearInterval(titleInterval);
      titleInterval = undefined;
    }
    document.title = originalTitle;

    // Reset favicon
    const favicon = document.querySelector('link[rel="icon"]') as HTMLLinkElement;
    if (favicon) {
      favicon.href = favicon.href.replace("?notification", "");
    }
  },
};