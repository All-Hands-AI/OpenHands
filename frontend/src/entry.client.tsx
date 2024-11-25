/* eslint-disable react/react-in-jsx-scope */
/**
 * By default, Remix will handle hydrating your app on the client for you.
 * You are free to delete this file if you'd like to, but if you ever want it revealed again, you can run `npx remix reveal` ✨
 * For more information, see https://remix.run/file-conventions/entry.client
 */

import { RemixBrowser } from "@remix-run/react";
import React, { startTransition, StrictMode } from "react";
import { hydrateRoot } from "react-dom/client";
import { Provider } from "react-redux";
import { PostHogProvider } from "posthog-js/react";
import "./i18n";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import store from "./store";
import { useConfig } from "./hooks/query/use-config";
import { AuthProvider } from "./context/auth-context";
import { UserPrefsProvider } from "./context/user-prefs-context";

function PosthogInit({ children }: React.PropsWithChildren) {
  const { data: config } = useConfig();

  // NOTE: The warning: [PostHog.js] was already loaded elsewhere. This may cause issues.
  // is caused due to React's strict mode. In production, this warning will not appear.
  return (
    <PostHogProvider
      apiKey={config?.POSTHOG_CLIENT_KEY}
      options={{
        api_host: "https://us.i.posthog.com",
        person_profiles: "identified_only",
      }}
    >
      {children}
    </PostHogProvider>
  );
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

const queryClient = new QueryClient();

prepareApp().then(() =>
  startTransition(() => {
    hydrateRoot(
      document,
      <StrictMode>
        <Provider store={store}>
          <UserPrefsProvider>
            <AuthProvider>
              <QueryClientProvider client={queryClient}>
                <PosthogInit>
                  <RemixBrowser />
                </PosthogInit>
              </QueryClientProvider>
            </AuthProvider>
          </UserPrefsProvider>
        </Provider>
      </StrictMode>,
    );
  }),
);
