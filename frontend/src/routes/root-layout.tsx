import React, { useEffect, useMemo, useState } from "react";
import {
  useRouteError,
  isRouteErrorResponse,
  Outlet,
  useLocation,
  useNavigation,
} from "react-router";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { useSettings } from "#/hooks/query/use-settings";
import { useBalance } from "#/hooks/query/use-balance";
import { useConfig } from "#/hooks/query/use-config";
import { LoadingOverlay } from "#/components/shared/loading-overlay";

export function ErrorBoundary() {
  const error = useRouteError();
  const { t } = useTranslation();

  if (isRouteErrorResponse(error)) {
    return (
      <div>
        <h1>{error.status}</h1>
        <p>{error.statusText}</p>
        <pre>
          {error.data instanceof Object
            ? JSON.stringify(error.data)
            : error.data}
        </pre>
      </div>
    );
  }
  if (error instanceof Error) {
    return (
      <div>
        <h1>{t(I18nKey.ERROR$GENERIC)}</h1>
        <pre>{error.message}</pre>
      </div>
    );
  }

  return (
    <div>
      <h1>{t(I18nKey.ERROR$UNKNOWN)}</h1>
    </div>
  );
}

export default function RootLayout() {
  const navigation = useNavigation();
  const location = useLocation();
  const [isNavigating, setIsNavigating] = useState(false);
  const config = useConfig();
  const balance = useBalance();
  const settings = useSettings();

  useEffect(() => {
    if (navigation.state !== "idle") {
      setIsNavigating(true);
    } else {
      const id = setTimeout(() => setIsNavigating(false), 150);
      return () => clearTimeout(id);
    }
  }, [navigation.state, location.pathname]);

  // Prefetch heavy route chunks optimistically
  useEffect(() => {
    const links = [
      "/conversations/:id/terminal",
      "/conversations/:id/jupyter",
      "/conversations/:id/browser",
      "/conversations/:id/served",
      "/chat",
      "/settings",
    ];
    for (const href of links) {
      const link = document.createElement("link");
      link.rel = "prefetch";
      link.as = "script";
      link.href = href; // react-router build maps chunks to route entries
      document.head.appendChild(link);
    }
    return () => {
      const toRemove = document.querySelectorAll('link[rel="prefetch"]');
      toRemove.forEach((el) => el.parentElement?.removeChild(el));
    };
  }, []);

  const showGlobalLoader = useMemo(() => {
    const isFetchingAuth = false; // plug actual auth query if available
    const isFetchingSettings = settings.isFetching;
    const isFetchingBalance = balance.isFetching;
    return (
      isNavigating || isFetchingAuth || isFetchingSettings || isFetchingBalance || config.isLoading
    );
  }, [isNavigating, settings.isFetching, balance.isFetching, config.isLoading]);

  const loaderMessage = isNavigating ? "Loading..." : (settings.isFetching ? "Loading settings..." : undefined);

  return (
    <div className="h-full w-full">
      <LoadingOverlay visible={showGlobalLoader} message={loaderMessage} />
      <Outlet />
    </div>
  );
}
