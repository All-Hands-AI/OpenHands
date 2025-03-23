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
import store from "./store";
import { useConfig } from "./hooks/query/use-config";
import { AuthProvider } from "./context/auth-context";
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

// Create a stable query client instance
export const queryClient = new QueryClient(queryClientConfig);

// Create the app element
const App = (
  <StrictMode>
    <Provider store={store}>
      <AuthProvider>
        <QueryClientProvider client={queryClient}>
          <HydratedRouter />
          <PosthogInit />
        </QueryClientProvider>
      </AuthProvider>
    </Provider>
  </StrictMode>
);

// Use a module-level variable to track if hydration has been attempted
let hasHydrated = false;

// Function to hydrate the app
const hydrateApp = () => {
  // Only attempt hydration once
  if (hasHydrated) return;
  hasHydrated = true;

  // Ensure we're in a browser environment
  if (typeof window === "undefined") return;

  // Use startTransition to avoid blocking the main thread
  startTransition(() => {
    try {
      // Find the root element - React Router might be looking for this specific element
      const rootElement = document.getElementById("root");
      if (rootElement) {
        // Hydrate the root element instead of the entire document
        hydrateRoot(rootElement, App);
      } else {
        // Fallback to document if root element is not found
        hydrateRoot(document, App);
      }
    } catch (error) {
      // Log hydration errors but don't rethrow
      // eslint-disable-next-line no-console
      console.error("Error during hydration:", error);
    }
  });
};

// Initialize the app
prepareApp().then(hydrateApp);
