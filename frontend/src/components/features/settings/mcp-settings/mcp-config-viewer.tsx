import React from "react";
import { useTranslation } from "react-i18next";
import { MCPConfig, MCPSSEServer, MCPStdioServer } from "#/types/settings";
import { I18nKey } from "#/i18n/declaration";

interface MCPConfigViewerProps {
  mcpConfig?: MCPConfig;
}

interface SSEServerDisplayProps {
  server: string | MCPSSEServer;
}

function SSEServerDisplay({ server }: SSEServerDisplayProps) {
  const { t } = useTranslation();

  if (typeof server === "string") {
    return (
      <div className="mb-2 p-2 bg-base-tertiary rounded-md">
        <div className="text-sm">
          <span className="font-medium">{t(I18nKey.SETTINGS$MCP_URL)}:</span>{" "}
          {server}
        </div>
      </div>
    );
  }

  return (
    <div className="mb-2 p-2 bg-base-tertiary rounded-md">
      <div className="text-sm">
        <span className="font-medium">{t(I18nKey.SETTINGS$MCP_URL)}:</span>{" "}
        {server.url}
      </div>
      {server.api_key && (
        <div className="text-sm text-gray-500">
          <span className="font-medium">
            {t(I18nKey.SETTINGS$MCP_API_KEY)}:
          </span>{" "}
          {server.api_key ? "Set" : t(I18nKey.SETTINGS$MCP_API_KEY_NOT_SET)}
        </div>
      )}
    </div>
  );
}

interface StdioServerDisplayProps {
  server: MCPStdioServer;
}

function StdioServerDisplay({ server }: StdioServerDisplayProps) {
  const { t } = useTranslation();

  return (
    <div className="mb-2 p-2 bg-base-tertiary rounded-md">
      <div className="text-sm">
        <span className="font-medium">{t(I18nKey.SETTINGS$MCP_NAME)}:</span>{" "}
        {server.name}
      </div>
      <div className="text-sm text-gray-500">
        <span className="font-medium">{t(I18nKey.SETTINGS$MCP_COMMAND)}:</span>{" "}
        {server.command}
      </div>
      {server.args && server.args.length > 0 && (
        <div className="text-sm text-gray-500">
          <span className="font-medium">{t(I18nKey.SETTINGS$MCP_ARGS)}:</span>{" "}
          {server.args.join(" ")}
        </div>
      )}
      {server.env && Object.keys(server.env).length > 0 && (
        <div className="text-sm text-gray-500">
          <span className="font-medium">{t(I18nKey.SETTINGS$MCP_ENV)}:</span>{" "}
          {Object.entries(server.env)
            .map(([key, value]) => `${key}=${value}`)
            .join(", ")}
        </div>
      )}
    </div>
  );
}

export function MCPConfigViewer({ mcpConfig }: MCPConfigViewerProps) {
  const { t } = useTranslation();

  if (
    !mcpConfig ||
    (mcpConfig.sse_servers.length === 0 && mcpConfig.stdio_servers.length === 0)
  ) {
    return null;
  }

  return (
    <div className="mt-4 border border-base-tertiary rounded-md p-3">
      <div className="flex justify-between items-center mb-3">
        <h3 className="text-sm font-medium">
          {t(I18nKey.SETTINGS$MCP_CONFIGURATION)}
        </h3>
        <a
          href="https://docs.all-hands.dev/usage/mcp"
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs text-blue-400 hover:underline"
          onClick={(e) => e.stopPropagation()}
        >
          {t(I18nKey.SETTINGS$MCP_LEARN_MORE)}
        </a>
      </div>

      <div className="mt-2">
        <div className="flex flex-col gap-4">
          {mcpConfig.sse_servers.length > 0 && (
            <div className="mb-3">
              <h4 className="text-sm font-medium mb-1">
                {t(I18nKey.SETTINGS$MCP_SSE_SERVERS)}{" "}
                <span className="text-gray-500">
                  ({mcpConfig.sse_servers.length})
                </span>
              </h4>
              {mcpConfig.sse_servers.map((server, index) => (
                <SSEServerDisplay key={`sse-${index}`} server={server} />
              ))}
            </div>
          )}

          {mcpConfig.stdio_servers.length > 0 && (
            <div>
              <h4 className="text-sm font-medium mb-1">
                {t(I18nKey.SETTINGS$MCP_STDIO_SERVERS)}{" "}
                <span className="text-gray-500">
                  ({mcpConfig.stdio_servers.length})
                </span>
              </h4>
              {mcpConfig.stdio_servers.map((server, index) => (
                <StdioServerDisplay key={`stdio-${index}`} server={server} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
