import * as React from "react";
import ReactDOM from "react-dom/client";
import "./index.css";
import { Provider } from "react-redux";
import { NextUIProvider } from "@nextui-org/react";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import App from "./App";
import reportWebVitals from "./reportWebVitals";
import store from "#/store";
import "#/i18n";
import RootLayout, { loader as rootLayoutLoader } from "./routes/RootLayout";
import Home, {
  action as homeAction,
  loader as homeLoader,
} from "./routes/Home/Home";
import { action as settingsAction } from "./routes/Settings";
import ConnectToGitHubModal from "./components/modals/ConnectToGitHubModal";
import WaitlistModal from "./components/modals/WaitlistModal";
import InactivityModal from "./components/modals/InactivityModal";
import AccountSettingsModal from "./components/modals/AccountSettingsModal";

const router = createBrowserRouter([
  {
    path: "/settings",
    action: settingsAction,
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
  {
    path: "/test",
    element: (
      <div className="flex items-center justify-center">
        <AccountSettingsModal />
      </div>
    ),
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
