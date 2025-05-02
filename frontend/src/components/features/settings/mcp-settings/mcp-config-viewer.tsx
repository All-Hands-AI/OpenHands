import React from "react";
import { useTranslation } from "react-i18next";
import { MCPConfig, MCPSSEServer, MCPStdioServer } from "#/types/settings";
import { I18nKey } from "#/i18n/declaration";

interface MCPConfigViewerProps {
  mcpConfig?: MCPConfig;
}

export function MCPConfigViewer({ mcpConfig }: MCPConfigViewerProps) {
  const { t } = useTranslation();

  if (
    !mcpConfig ||
    (mcpConfig.sse_servers.length === 0 && mcpConfig.stdio_servers.length === 0)
  ) {
    return null;
  }

  const renderSSEServer = (server: string | MCPSSEServer, index: number) => {
    if (typeof server === "string") {
      return (
        <div
          key={`sse-${index}`}
          className="mb-2 p-2 bg-base-tertiary rounded-md"
        >
          <div className="text-sm font-medium">
            {t(I18nKey.SETTINGS$MCP_URL)}: {server}
          </div>
        </div>
      );
    }
    return (
      <div
        key={`sse-${index}`}
        className="mb-2 p-2 bg-base-tertiary rounded-md"
      >
        <div className="text-sm font-medium">
          {t(I18nKey.SETTINGS$MCP_URL)}: {server.url}
        </div>
        {server.api_key && (
          <div className="text-xs text-gray-400">
            {t(I18nKey.SETTINGS$MCP_API_KEY)}:{" "}
            {server.api_key ? "Set" : t(I18nKey.SETTINGS$MCP_API_KEY_NOT_SET)}
          </div>
        )}
      </div>
    );
  };

  const renderStdioServer = (server: MCPStdioServer, index: number) => (
    <div
      key={`stdio-${index}`}
      className="mb-2 p-2 bg-base-tertiary rounded-md"
    >
      <div className="text-sm font-medium">
        {t(I18nKey.SETTINGS$MCP_NAME)}: {server.name}
      </div>
      <div className="text-xs">
        {t(I18nKey.SETTINGS$MCP_COMMAND)}: {server.command}
      </div>
      {server.args && server.args.length > 0 && (
        <div className="text-xs">
          {t(I18nKey.SETTINGS$MCP_ARGS)}: {server.args.join(" ")}
        </div>
      )}
      {server.env && Object.keys(server.env).length > 0 && (
        <div className="text-xs">
          {t(I18nKey.SETTINGS$MCP_ENV)}:{" "}
          {Object.entries(server.env)
            .map(([key, value]) => `${key}=${value}`)
            .join(", ")}
        </div>
      )}
    </div>
  );

  return (
    <div className="mt-4 border border-base-tertiary rounded-md p-3">
      <div className="flex justify-between items-center mb-3">
        <h3 className="text-sm font-medium">
          {t(I18nKey.SETTINGS$MCP_CONFIGURATION)}
        </h3>
        <a
          href="https://docs.all-hands.dev/modules/usage/mcp"
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs text-blue-400 hover:underline"
          onClick={(e) => e.stopPropagation()}
        >
          {t(I18nKey.SETTINGS$MCP_LEARN_MORE)}
        </a>
      </div>

      <div className="mt-2">
        {mcpConfig.sse_servers.length > 0 && (
          <div className="mb-3">
            <h4 className="text-xs font-medium mb-1">
              {t(I18nKey.SETTINGS$MCP_SSE_SERVERS)}
            </h4>
            {mcpConfig.sse_servers.map(renderSSEServer)}
          </div>
        )}

        {mcpConfig.stdio_servers.length > 0 && (
          <div>
            <h4 className="text-xs font-medium mb-1">
              {t(I18nKey.SETTINGS$MCP_STDIO_SERVERS)}
            </h4>
            {mcpConfig.stdio_servers.map(renderStdioServer)}
          </div>
        )}
      </div>
    </div>
  );
}
