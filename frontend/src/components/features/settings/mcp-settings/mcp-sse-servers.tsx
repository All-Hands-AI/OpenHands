import React from "react";
import { useTranslation } from "react-i18next";
import { MCPSSEServer } from "#/types/settings";
import { I18nKey } from "#/i18n/declaration";

interface MCPSSEServersProps {
  servers: (string | MCPSSEServer)[];
}

export function MCPSSEServers({ servers }: MCPSSEServersProps) {
  const { t } = useTranslation();

  return (
    <div>
      <h4 className="text-sm font-medium mb-2">
        {t(I18nKey.SETTINGS$MCP_SSE_SERVERS)}{" "}
        <span className="text-gray-500">({servers.length})</span>
      </h4>
      {servers.map((server, index) => (
        <div
          key={`sse-${index}`}
          className="mb-2 p-2 bg-base-tertiary rounded-md"
        >
          <div className="text-sm">
            <span className="font-medium">{t(I18nKey.SETTINGS$MCP_URL)}:</span>{" "}
            {typeof server === "string" ? server : server.url}
          </div>
          {typeof server !== "string" && server.api_key && (
            <div className="mt-1 text-sm text-gray-500">
              <span className="font-medium">
                {t(I18nKey.SETTINGS$MCP_API_KEY)}:
              </span>{" "}
              {server.api_key
                ? "Configured"
                : t(I18nKey.SETTINGS$MCP_API_KEY_NOT_SET)}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
