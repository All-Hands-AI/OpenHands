/* eslint-disable react/react-in-jsx-scope */
/**
 * By default, Remix will handle hydrating your app on the client for you.
 * You are free to delete this file if you'd like to, but if you ever want it revealed again, you can run `npx remix reveal` ✨
 * For more information, see https://remix.run/file-conventions/entry.client
 */

import { HydratedRouter } from "react-router/dom";
import React, { startTransition, StrictMode } from "react";
import { hydrateRoot } from "react-dom/client";
import { Provider } from "react-redux";
import posthog from "posthog-js";
import "./i18n";
import { QueryClientProvider } from "@tanstack/react-query";
import store from "./store";
import OpenHands from "./api/open-hands";
import { displayErrorToast } from "./utils/custom-toast-handlers";
import { queryClient } from "./query-client-config";
import { io } from "socket.io-client";

// Initialize your socket connection here
const socket = io("wss://mojocode.sixtyoneeighty.com", {
  transports: ["websocket", "polling"],
  query: {
    conversation_id: "c8c00e95728f4acda5666c0dfce221d0" // <-- Put your real conversation ID here
  }
});

socket.on("connect", () => {
  console.log("Connected to Socket.IO!", socket.id);
});

socket.on("connect_error", (err) => {
  console.error("Socket.IO connect error:", err);
});

// (You can export socket here if you want to use it elsewhere)
export { socket };

function PosthogInit() {
  const [posthogClientKey, setPosthogClientKey] = React.useState<string | null>(
    null,
  );

  React.useEffect(() => {
    (async () => {
      try {
        const config = await OpenHands.getConfig();
        setPosthogClientKey(config.POSTHOG_CLIENT_KEY);
      } catch (error) {
        displayErrorToast("Error fetching PostHog client key");
      }
    })();
  }, []);

  React.useEffect(() => {
    // Check if we're in development mode using import.meta.env (Vite) or process.env
    const isDevelopment =
      import.meta.env.DEV || process.env.NODE_ENV === "development";
    const isProduction =
      import.meta.env.PROD || process.env.NODE_ENV === "production";

    console.log(
      "PostHog init - isDevelopment:",
      isDevelopment,
      "isProduction:",
      isProduction,
      "clientKey:",
      !!posthogClientKey,
    );

    // Add global error handler to catch PostHog network errors
    const originalConsoleError = console.error;
    console.error = function (...args) {
      const message = args.join(" ");
      // Filter out PostHog-related network errors
      if (
        message.includes("posthog.com") &&
        message.includes("ERR_BLOCKED_BY_CLIENT")
      ) {
        console.debug(
          "PostHog request blocked by ad blocker or privacy extension",
        );
        return;
      }
      originalConsoleError.apply(console, args);
    };

    if (posthogClientKey && isProduction && !isDevelopment) {
      // Only initialize PostHog in production to avoid development network errors
      try {
        posthog.init(posthogClientKey, {
          api_host: "https://us.i.posthog.com",
          person_profiles: "identified_only",
          disable_session_recording: false,
          loaded: () => {
            console.log("PostHog loaded successfully");
          },
        });

        // Override PostHog methods to handle blocked requests gracefully
        const originalCapture = posthog.capture;
        posthog.capture = function (eventName, properties, options) {
          try {
            return originalCapture.call(this, eventName, properties, options);
          } catch (error) {
            console.debug(
              "PostHog request blocked by ad blocker or privacy extension",
            );
            return undefined;
          }
        };

        const originalIdentify = posthog.identify;
        posthog.identify = function (
          distinctId,
          userProperties,
          userPropertiesOnce,
        ) {
          try {
            return originalIdentify.call(
              this,
              distinctId,
              userProperties,
              userPropertiesOnce,
            );
          } catch (error) {
            console.debug(
              "PostHog identify blocked by ad blocker or privacy extension",
            );
            return undefined;
          }
        };
      } catch (error) {
        console.debug(
          "PostHog initialization blocked by ad blocker or privacy extension",
        );
        // Create a mock posthog object when blocked
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        (window as any).posthog = {
          init: () => {},
          capture: () => {},
          identify: () => {},
          reset: () => {},
          isFeatureEnabled: () => false,
          onFeatureFlags: () => {},
          people: { set: () => {} },
          debug: () => {},
          sessionRecording: { sessionId: "", windowId: "" },
          has_opted_out_capturing: () => false,
          captureException: () => {},
        };
      }
    } else if (posthogClientKey) {
      // In development or when not in production, create a mock PostHog instance to avoid network errors
      console.log(
        "PostHog disabled in development mode to prevent network errors",
      );
      // Create a mock posthog object with no-op methods
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (window as any).posthog = {
        init: () => {},
        capture: () => {},
        identify: () => {},
        reset: () => {},
        isFeatureEnabled: () => false,
        onFeatureFlags: () => {},
        people: { set: () => {} },
        debug: () => {},
        sessionRecording: { sessionId: "", windowId: "" },
        has_opted_out_capturing: () => false,
        captureException: () => {},
      };
    }
  }, [posthogClientKey]);

  return null;
}

async function prepareApp() {
  if (
    process.env.NODE_ENV === "development" &&
    import.meta.env.VITE_MOCK_API === "true"
  ) {
    const { worker } = await import("./mocks/browser");

    await worker.start({
      onUnhandledRequest: "bypass",
    });
  }
}

prepareApp().then(() =>
  startTransition(() => {
    hydrateRoot(
      document,
      <StrictMode>
        <Provider store={store}>
          <QueryClientProvider client={queryClient}>
            <PosthogInit />
            <HydratedRouter />
          </QueryClientProvider>
        </Provider>
      </StrictMode>,
    );
  }),
);
