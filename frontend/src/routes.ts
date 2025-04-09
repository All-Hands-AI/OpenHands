import {
  type RouteConfig,
  layout,
  index,
  route,
} from "@react-router/dev/routes";

export default [
  layout("routes/_oh/route.tsx", [
    index("routes/_oh._index/route.tsx"),
    route("settings", "routes/settings.tsx", [
      index("routes/account-settings.tsx"),
      route("billing", "routes/billing.tsx"),
    ]),
    route("conversations/:conversationId", "routes/_oh.app/route.tsx", [
      index("routes/_oh.app._index/route.tsx"),
      route("browser", "routes/_oh.app.browser.tsx"),
      route("jupyter", "routes/_oh.app.jupyter.tsx"),
      route("terminal", "routes/_oh.app.terminal.tsx"),
      route("served", "routes/app.tsx"),
    ]),
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
] satisfies RouteConfig;
