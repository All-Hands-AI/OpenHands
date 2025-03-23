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
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import store from "./store";
import { useConfig } from "./hooks/query/use-config";
import { AuthProvider } from "./context/auth-context";
import { FileStateProvider } from "./context/file-state-context";
import { queryClientConfig } from "./query-client-config";

function PosthogInit() {
  const { data: config } = useConfig();

  React.useEffect(() => {
    if (config?.POSTHOG_CLIENT_KEY) {
      posthog.init(config.POSTHOG_CLIENT_KEY, {
        api_host: "https://us.i.posthog.com",
        person_profiles: "identified_only",
      });
    }
  }, [config]);

  return null;
}

/**
 * Conditionally renders React Query Devtools in development mode
 */
function ReactQueryDevtoolsProduction() {
  const [showDevtools, setShowDevtools] = React.useState(false);

  React.useEffect(() => {
    // Only show devtools in development
    if (process.env.NODE_ENV === 'development') {
      setShowDevtools(true);
    } else {
      // In production, only show devtools when pressing ctrl+shift+q
      window.addEventListener('keydown', (event) => {
        if (event.ctrlKey && event.shiftKey && event.key === 'q') {
          setShowDevtools((prev) => !prev);
        }
      });
    }
  }, []);

  return showDevtools ? <ReactQueryDevtools initialIsOpen={false} /> : null;
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

export const queryClient = new QueryClient(queryClientConfig);

prepareApp().then(() =>
  startTransition(() => {
    hydrateRoot(
      document,
      <StrictMode>
        <Provider store={store}>
          <AuthProvider>
            <QueryClientProvider client={queryClient}>
              <FileStateProvider>
                <HydratedRouter />
                <PosthogInit />
                <ReactQueryDevtoolsProduction />
              </FileStateProvider>
            </QueryClientProvider>
          </AuthProvider>
        </Provider>
      </StrictMode>,
    );
  }),
);
