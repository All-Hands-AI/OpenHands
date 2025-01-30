import React from "react";
import { createRoot } from "react-dom/client";
import { Provider } from "react-redux";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import posthog from "posthog-js";
import "./i18n";
import store from "./store";
import { useConfig } from "./hooks/query/use-config";
import { AuthProvider } from "./context/auth-context";
import { queryClientConfig } from "./query-client-config";
import { SettingsProvider } from "./context/settings-context";
import App from "./root";

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

const queryClient = new QueryClient(queryClientConfig);

prepareApp().then(() => {
  const container = document.getElementById("root");
  if (!container) throw new Error("#root element not found");

  const root = createRoot(container);
  root.render(
    <React.StrictMode>
      <Provider store={store}>
        <AuthProvider>
          <QueryClientProvider client={queryClient}>
            <SettingsProvider>
              <BrowserRouter>
                <App />
                <PosthogInit />
              </BrowserRouter>
            </SettingsProvider>
          </QueryClientProvider>
        </AuthProvider>
      </Provider>
    </React.StrictMode>,
  );
});
