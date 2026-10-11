import { useTranslation } from "react-i18next";
import { useQuery } from "@tanstack/react-query";

import { ServerClient } from "@openhands/typescript-client/clients";
import { type Backend } from "#/api/backend-registry/types";
import { getAgentServerClientOptions } from "#/api/agent-server-client-options";
import { getDisplayAgentServerVersion } from "#/api/agent-server-compatibility";
import { fetchBackendExecutionRuntime } from "#/api/agent-server-adapter";
import { I18nKey } from "#/i18n/declaration";

function getExecutionModeLabel(
  t: (key: I18nKey) => string,
  mode: "local" | "docker",
): string {
  if (mode === "local") {
    return t(I18nKey.BACKEND$EXECUTION_MODE_LOCAL);
  }
  if (mode === "docker") {
    return t(I18nKey.BACKEND$EXECUTION_MODE_DOCKER);
  }
  return mode;
}

// @spec BM-004 — Display active backend execution runtime
export function BackendVersion({ backend }: { backend: Backend }) {
  const { t } = useTranslation("openhands");
  const { data } = useQuery({
    queryKey: ["backend-version", backend.host, backend.apiKey],
    queryFn: async () => {
      const clientOptions = {
        host: backend.host,
        sessionApiKey: backend.apiKey || null,
        timeout: 5000,
      };
      const [info, executionRuntime] = await Promise.all([
        new ServerClient(
          getAgentServerClientOptions(clientOptions),
        ).getServerInfo(),
        fetchBackendExecutionRuntime(clientOptions),
      ]);
      return {
        version: getDisplayAgentServerVersion(info),
        executionRuntime: executionRuntime ?? null,
      };
    },
    retry: false,
    staleTime: 60_000,
    enabled: backend.kind === "local",
  });

  if (!data?.version) return null;

  return (
    <>
      <span
        className="inline-flex shrink-0 items-center rounded-full border border-border bg-surface px-1.5 py-0.5 text-[10px] font-medium leading-none text-text-dim"
        data-testid={`manage-backends-version-${backend.name}`}
      >
        {t(I18nKey.BACKEND$VERSION_LABEL, { version: data.version })}
      </span>
      {data.executionRuntime ? (
        <span
          className="inline-flex shrink-0 items-center rounded-full border border-border bg-surface px-1.5 py-0.5 text-[10px] font-medium leading-none text-text-dim"
          data-testid={`manage-backends-mode-${backend.name}`}
        >
          {getExecutionModeLabel(t, data.executionRuntime)}
        </span>
      ) : null}
    </>
  );
}
