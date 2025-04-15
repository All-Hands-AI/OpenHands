import {
  type RouteConfig,
  layout,
  index,
  route,
} from "@react-router/dev/routes"

export default [
  layout("routes/root-layout.tsx", [
    index("routes/home.tsx"),
    route("settings", "routes/settings.tsx", [
      index("routes/account-settings.tsx"),
      route("billing", "routes/billing.tsx"),
    ]),

    route("conversations/:conversationId", "routes/conversation.tsx", [
      index("routes/editor-tab.tsx"),
      route("browser", "routes/browser-tab.tsx"),
      route("jupyter", "routes/jupyter-tab.tsx"),
      route("terminal", "routes/terminal-tab.tsx"),
      route("served", "routes/served-tab.tsx"),
    ]),
    route("share/:conversationId", "routes/share.tsx"),
    route(
      "shares/conversations/:conversationId",
      "routes/_oh.share.app/route.tsx",
      [
        index("routes/_oh.share.app._index/route.tsx"),
        route("browser", "routes/nested-share-routes/_oh.app.browser.tsx"),
        route("jupyter", "routes/nested-share-routes/_oh.app.jupyter.tsx"),
        route("terminal", "routes/nested-share-routes/_oh.app.terminal.tsx"),
        // route("served", "routes/app.tsx"),
      ],
    ),
  ]),
] satisfies RouteConfig
