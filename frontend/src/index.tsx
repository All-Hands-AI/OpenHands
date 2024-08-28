import * as React from "react";
import ReactDOM from "react-dom/client";
import "./index.css";
import { Provider } from "react-redux";
import { NextUIProvider } from "@nextui-org/react";
import {
  ActionFunctionArgs,
  createBrowserRouter,
  json,
  RouterProvider,
} from "react-router-dom";
import App from "./App";
import reportWebVitals from "./reportWebVitals";
import store from "#/store";
import "#/i18n";
import RootLayout, { loader as rootLayoutLoader } from "./routes/RootLayout";
import Home, {
  action as homeAction,
  loader as homeLoader,
} from "./routes/Home/Home";
import {
  getDefaultSettings,
  saveSettings,
  Settings,
} from "./services/settings";

const router = createBrowserRouter([
  {
    path: "/settings",
    action: async ({ request }: ActionFunctionArgs) => {
      const formData = await request.formData();
      const entries = Object.fromEntries(formData.entries());

      const intent = formData.get("intent")?.toString();

      if (intent === "reset") {
        saveSettings(getDefaultSettings());
        return json(null);
      }

      const USING_CUSTOM_MODEL =
        Object.keys(entries).includes("use-custom-model");
      const CUSTOM_LLM_MODEL = USING_CUSTOM_MODEL
        ? formData.get("custom-model")?.toString()
        : undefined;
      const LLM_MODEL = formData.get("model")?.toString();
      const LLM_API_KEY = formData.get("api-key")?.toString();
      const AGENT = formData.get("agent")?.toString();

      const settings: Partial<Settings> = {
        USING_CUSTOM_MODEL,
        CUSTOM_LLM_MODEL,
        LLM_MODEL,
        LLM_API_KEY,
        AGENT,
      };

      saveSettings(settings);
      return json(null);
    },
  },
  {
    path: "/",
    element: <RootLayout />,
    loader: rootLayoutLoader,
    children: [
      {
        path: "/",
        element: <Home />,
        loader: homeLoader,
        action: homeAction,
      },
      {
        path: "/app",
        element: <App />,
      },
    ],
  },
]);

const root = ReactDOM.createRoot(
  document.getElementById("root") as HTMLElement,
);

root.render(
  <React.StrictMode>
    <Provider store={store}>
      <NextUIProvider>
        <RouterProvider router={router} />
      </NextUIProvider>
    </Provider>
  </React.StrictMode>,
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
