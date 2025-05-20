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
    if (posthogClientKey) {
      posthog.init(posthogClientKey, {
        api_host: "https://us.i.posthog.com",
        person_profiles: "identified_only",
      });
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
            <HydratedRouter />
            <PosthogInit />
            <div id="modal-portal-exit" />
          </QueryClientProvider>
        </Provider>
      </StrictMode>,
    );
  }),
);
