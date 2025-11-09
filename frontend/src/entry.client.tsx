/* eslint-disable react/react-in-jsx-scope */
/**
 * By default, Remix will handle hydrating your app on the client for you.
 * You are free to delete this file if you'd like to, but if you ever want it revealed again, you can run `npx remix reveal` ✨
 * For more information, see https://remix.run/file-conventions/entry.client
 */

import { HydratedRouter } from "react-router/dom";
import React, { startTransition, StrictMode } from "react";
import { hydrateRoot } from "react-dom/client";
import posthog from "posthog-js";
import "./i18n";
import { QueryClientProvider } from "@tanstack/react-query";
import OptionService from "./api/option-service/option-service.api";
import { displayErrorToast } from "./utils/custom-toast-handlers";
import { queryClient } from "./query-client-config";

function PosthogInit() {
  const [posthogClientKey, setPosthogClientKey] = React.useState<string | null>(
    null,
  );

  React.useEffect(() => {
    (async () => {
      try {
        const config = await OptionService.getConfig();
        setPosthogClientKey(config.POSTHOG_CLIENT_KEY);
      } catch {
        displayErrorToast("Error fetching PostHog client key");
      }
    })();
  }, []);

  React.useEffect(() => {
    if (posthogClientKey) {
      posthog.init(posthogClientKey, {
        api_host: "https://us.i.posthog.com",
        person_profiles: "identified_only",
        opt_out_capturing_by_default: true, // Opt out by default until user consent is determined
        autocapture: false, // Disable automatic event capture
        capture_pageview: false, // Disable automatic pageview capture
        capture_pageleave: false, // Disable automatic pageleave capture
        loaded: (posthog) => {
          // Ensure we're opted out immediately after PostHog loads
          if (!posthog.has_opted_in_capturing()) {
            posthog.opt_out_capturing();
          }
        },
      });
      // Immediately opt out to prevent any tracking until consent is determined
      // This is a safety measure in case loaded callback hasn't fired yet
      posthog.opt_out_capturing();
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
        <QueryClientProvider client={queryClient}>
          <HydratedRouter />
          <PosthogInit />
        </QueryClientProvider>
        <div id="modal-portal-exit" />
      </StrictMode>,
    );
  }),
);
