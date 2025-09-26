/* eslint-disable react/react-in-jsx-scope */
/**
 * By default, Remix will handle hydrating your app on the client for you.
 * You are free to delete this file if you'd like to, but if you ever want it revealed again, you can run `npx remix reveal` ✨
 * For more information, see https://remix.run/file-conventions/entry.client
 */

import { HydratedRouter } from "react-router/dom";
import { useSearchParams } from "react-router";
import React, { startTransition, StrictMode } from "react";
import { hydrateRoot } from "react-dom/client";
import { Provider } from "react-redux";
import posthog, { PostHogConfig } from "posthog-js";
import "./i18n";
import { QueryClientProvider } from "@tanstack/react-query";
import store from "./store";
import OptionService from "./api/option-service/option-service.api";
import { displayErrorToast } from "./utils/custom-toast-handlers";
import { queryClient } from "./query-client-config";

function PosthogInit() {
  const [posthogClientKey, setPosthogClientKey] = React.useState<string | null>(
    null,
  );
  const [searchParams, setSearchParams] = useSearchParams();

  // If arriving from marketing with ph_did, store it as a short-lived cookie and clean the URL
  React.useEffect(() => {
    try {
      const phDid = searchParams.get("ph_did");
      if (phDid) {
        const expires = new Date(
          Date.now() + 1000 * 60 * 60 * 24,
        ).toUTCString(); // 1 day
        document.cookie = `ph_did=${encodeURIComponent(phDid)}; Path=/; Expires=${expires}; SameSite=Lax`;
        setSearchParams((prevParams) => {
          prevParams.delete("ph_did");
          return prevParams;
        });
      }
    } catch {
      // Ignore errors when parsing search params
    }
  }, [searchParams, setSearchParams]);

  React.useEffect(() => {
    (async () => {
      try {
        const config = await OptionService.getConfig();
        setPosthogClientKey(config.POSTHOG_CLIENT_KEY);
      } catch (error) {
        displayErrorToast("Error fetching PostHog client key");
      }
    })();
  }, []);

  React.useEffect(() => {
    if (posthogClientKey) {
      const opts: Partial<PostHogConfig> = {
        api_host: "https://us.i.posthog.com",
        person_profiles: "identified_only",
        cross_subdomain_cookie: true,
      };
      posthog.init(posthogClientKey, opts);
      // tag events with site identifier for segmentation
      posthog.register({ site: "app" });
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
          </QueryClientProvider>
        </Provider>
        <div id="modal-portal-exit" />
      </StrictMode>,
    );
  }),
);
