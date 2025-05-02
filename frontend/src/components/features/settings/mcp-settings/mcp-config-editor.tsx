import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { MCPConfig, MCPSSEServer, MCPStdioServer } from "#/types/settings";
import { I18nKey } from "#/i18n/declaration";

interface MCPConfigEditorProps {
  mcpConfig?: MCPConfig;
  onChange: (config: MCPConfig) => void;
}

export function MCPConfigEditor({ mcpConfig, onChange }: MCPConfigEditorProps) {
  const { t } = useTranslation();
  const [isEditing, setIsEditing] = useState(false);
  const [configText, setConfigText] = useState(() =>
    mcpConfig
      ? JSON.stringify(mcpConfig, null, 2)
      : t(I18nKey.SETTINGS$MCP_DEFAULT_CONFIG),
  );
  const [error, setError] = useState<string | null>(null);

  const toggleEdit = () => {
    if (isEditing) {
      // Save changes
      try {
        const newConfig = JSON.parse(configText);

        // Validate the structure
        if (!newConfig.sse_servers || !Array.isArray(newConfig.sse_servers)) {
          throw new Error(t(I18nKey.SETTINGS$MCP_ERROR_SSE_ARRAY));
        }

        if (
          !newConfig.stdio_servers ||
          !Array.isArray(newConfig.stdio_servers)
        ) {
          throw new Error(t(I18nKey.SETTINGS$MCP_ERROR_STDIO_ARRAY));
        }

        // Validate SSE servers
        for (const server of newConfig.sse_servers) {
          if (
            typeof server !== "string" &&
            (!server.url || typeof server.url !== "string")
          ) {
            throw new Error(t(I18nKey.SETTINGS$MCP_ERROR_SSE_URL));
          }
        }

        // Validate stdio servers
        for (const server of newConfig.stdio_servers) {
          if (!server.name || !server.command) {
            throw new Error(t(I18nKey.SETTINGS$MCP_ERROR_STDIO_PROPS));
          }
        }

        onChange(newConfig);
        setError(null);
      } catch (e) {
        setError(
          e instanceof Error
            ? e.message
            : t(I18nKey.SETTINGS$MCP_ERROR_INVALID_JSON),
        );
        return; // Don't exit edit mode if there's an error
      }
    }

    setIsEditing(!isEditing);
  };

  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setConfigText(e.target.value);
  };

  const renderSSEServer = (server: string | MCPSSEServer, index: number) => {
    if (typeof server === "string") {
      return (
        <div
          key={`sse-${index}`}
          className="mb-2 p-2 bg-base-tertiary rounded-md"
        >
          <div className="text-sm">
            <span className="font-medium">
              {t(I18nKey.SETTINGS$MCP_SSE_SERVERS)}:
            </span>{" "}
            {server}
          </div>
        </div>
      );
    }
    return (
      <div
        key={`sse-${index}`}
        className="mb-2 p-2 bg-base-tertiary rounded-md"
      >
        <div className="text-sm">
          <span className="font-medium">
            {t(I18nKey.SETTINGS$MCP_SSE_SERVERS)}:
          </span>{" "}
          {server.url}
        </div>
        {server.api_key && (
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
    );
  };

  const renderStdioServer = (server: MCPStdioServer, index: number) => (
    <div
      key={`stdio-${index}`}
      className="mb-2 p-2 bg-base-tertiary rounded-md"
    >
      <div className="text-sm">
        <span className="font-medium">{t(I18nKey.SETTINGS$MCP_NAME)}:</span>{" "}
        {server.name}
      </div>
      <div className="mt-1 text-sm text-gray-500">
        <span className="font-medium">{t(I18nKey.SETTINGS$MCP_COMMAND)}:</span>{" "}
        <code className="font-mono">{server.command}</code>
      </div>
      {server.args && server.args.length > 0 && (
        <div className="mt-1 text-sm text-gray-500">
          <span className="font-medium">{t(I18nKey.SETTINGS$MCP_ARGS)}:</span>{" "}
          <code className="font-mono">{server.args.join(" ")}</code>
        </div>
      )}
      {server.env && Object.keys(server.env).length > 0 && (
        <div className="mt-1 text-sm text-gray-500">
          <span className="font-medium">{t(I18nKey.SETTINGS$MCP_ENV)}:</span>{" "}
          <code className="font-mono">
            {Object.entries(server.env)
              .map(([key, value]) => `${key}=${value}`)
              .join(", ")}
          </code>
        </div>
      )}
    </div>
  );

  const config = mcpConfig || { sse_servers: [], stdio_servers: [] };

  return (
    <div>
      <div className="flex justify-between items-center mb-3">
        <div className="text-sm font-medium">
          {t(I18nKey.SETTINGS$MCP_CONFIGURATION)}
        </div>
        <div className="flex items-center">
          <a
            href="https://docs.all-hands.dev/modules/usage/mcp"
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-blue-400 hover:underline mr-3"
            onClick={(e) => e.stopPropagation()}
          >
            Documentation
          </a>
          <button
            type="button"
            className="text-xs bg-blue-500 text-white px-2 py-1 rounded-md hover:bg-blue-600"
            onClick={toggleEdit}
          >
            {isEditing
              ? t(I18nKey.SETTINGS$MCP_APPLY_CHANGES)
              : t(I18nKey.SETTINGS$MCP_EDIT_CONFIGURATION)}
          </button>
        </div>
      </div>

      <div>
        {isEditing ? (
          <div>
            <div className="mb-2 text-sm text-gray-400">
              {t(I18nKey.SETTINGS$MCP_CONFIG_DESCRIPTION)}
            </div>
            <textarea
              className="w-full h-64 p-2 text-sm font-mono bg-base-tertiary rounded-md focus:border-blue-500 focus:outline-none"
              value={configText}
              onChange={handleTextChange}
              spellCheck="false"
            />
            {error && (
              <div className="mt-2 p-2 bg-red-100 border border-red-300 rounded-md text-sm text-red-700">
                <strong>{t(I18nKey.SETTINGS$MCP_CONFIG_ERROR)}</strong> {error}
              </div>
            )}
            <div className="mt-2 text-sm text-gray-400">
              <strong>{t(I18nKey.SETTINGS$MCP_CONFIG_EXAMPLE)}</strong>{" "}
              <code>
                {
                  '{ "sse_servers": ["https://example-mcp-server.com/sse"], "stdio_servers": [{ "name": "fetch", "command": "uvx", "args": ["mcp-server-fetch"] }] }'
                }
              </code>
            </div>
          </div>
        ) : (
          <>
            <div className="flex flex-col gap-4">
              <div className="mb-3">
                <h4 className="text-sm font-medium mb-1">
                  {t(I18nKey.SETTINGS$MCP_SSE_SERVERS)}{" "}
                  <span className="text-gray-500">
                    ({config.sse_servers.length})
                  </span>
                </h4>
                {config.sse_servers.length > 0 ? (
                  config.sse_servers.map(renderSSEServer)
                ) : (
                  <div className="p-2 bg-base-tertiary rounded-md text-sm text-gray-400">
                    {t(I18nKey.SETTINGS$MCP_NO_SSE_SERVERS)}
                  </div>
                )}
              </div>

              <div>
                <h4 className="text-sm font-medium mb-1">
                  {t(I18nKey.SETTINGS$MCP_STDIO_SERVERS)}{" "}
                  <span className="text-gray-500">
                    ({config.stdio_servers.length})
                  </span>
                </h4>
                {config.stdio_servers.length > 0 ? (
                  config.stdio_servers.map(renderStdioServer)
                ) : (
                  <div className="p-2 bg-base-tertiary rounded-md text-sm text-gray-400">
                    {t(I18nKey.SETTINGS$MCP_NO_STDIO_SERVERS)}
                  </div>
                )}
              </div>
            </div>

            {config.sse_servers.length === 0 &&
              config.stdio_servers.length === 0 && (
                <div className="mt-2 p-2 bg-yellow-50 border border-yellow-200 rounded-md text-sm text-yellow-700">
                  {t(I18nKey.SETTINGS$MCP_NO_SERVERS_CONFIGURED)}
                </div>
              )}
          </>
        )}
      </div>
    </div>
  );
}
