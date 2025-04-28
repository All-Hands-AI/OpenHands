import {
  type RouteConfig,
  layout,
  index,
  route,
} from "@react-router/dev/routes";

export default [
  layout("routes/root-layout.tsx", [
    index("routes/home.tsx"),
    route("settings", "routes/settings.tsx", [
      index("routes/account-settings.tsx"),
      route("billing", "routes/billing.tsx"),
      route("api-keys", "routes/api-keys.tsx"),
    ]),
    route("conversations/:conversationId", "routes/conversation.tsx", [
      index("routes/editor.tsx"),
      route("browser", "routes/browser-tab.tsx"),
      route("jupyter", "routes/jupyter-tab.tsx"),
      route("served", "routes/served-tab.tsx"),
      route("terminal", "routes/terminal-tab.tsx"),
      route("vscode", "routes/vscode-tab.tsx"),
    ]),
  ]),
] satisfies RouteConfig;
