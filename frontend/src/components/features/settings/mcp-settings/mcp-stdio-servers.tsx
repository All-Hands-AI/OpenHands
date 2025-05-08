import React from "react";
import { useTranslation } from "react-i18next";
import { MCPStdioServer } from "#/types/settings";
import { I18nKey } from "#/i18n/declaration";

interface MCPStdioServersProps {
  servers: MCPStdioServer[];
}

export function MCPStdioServers({ servers }: MCPStdioServersProps) {
  const { t } = useTranslation();

  return (
    <div>
      <h4 className="text-sm font-medium mb-2">
        {t(I18nKey.SETTINGS$MCP_STDIO_SERVERS)}{" "}
        <span className="text-gray-500">({servers.length})</span>
      </h4>
      {servers.map((server, index) => (
        <div
          key={`stdio-${index}`}
          className="mb-2 p-2 bg-base-tertiary rounded-md"
        >
          <div className="text-sm">
            <span className="font-medium">{t(I18nKey.SETTINGS$MCP_NAME)}:</span>{" "}
            {server.name}
          </div>
          <div className="mt-1 text-sm text-gray-500">
            <span className="font-medium">
              {t(I18nKey.SETTINGS$MCP_COMMAND)}:
            </span>{" "}
            <code className="font-mono">{server.command}</code>
          </div>
          {server.args && server.args.length > 0 && (
            <div className="mt-1 text-sm text-gray-500">
              <span className="font-medium">
                {t(I18nKey.SETTINGS$MCP_ARGS)}:
              </span>{" "}
              <code className="font-mono">{server.args.join(" ")}</code>
            </div>
          )}
          {server.env && Object.keys(server.env).length > 0 && (
            <div className="mt-1 text-sm text-gray-500">
              <span className="font-medium">
                {t(I18nKey.SETTINGS$MCP_ENV)}:
              </span>{" "}
              <code className="font-mono">
                {Object.entries(server.env)
                  .map(([key, value]) => `${key}=${value}`)
                  .join(", ")}
              </code>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
