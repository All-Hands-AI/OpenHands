import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { MCPConfig } from "#/types/settings";
import { I18nKey } from "#/i18n/declaration";
import { BrandButton } from "../brand-button";

interface MCPJsonEditorProps {
  mcpConfig?: MCPConfig;
  onChange: (config: MCPConfig) => void;
}

export function MCPJsonEditor({ mcpConfig, onChange }: MCPJsonEditorProps) {
  const { t } = useTranslation();
  const [configText, setConfigText] = useState(() =>
    mcpConfig
      ? JSON.stringify(mcpConfig, null, 2)
      : t(I18nKey.SETTINGS$MCP_DEFAULT_CONFIG),
  );
  const [error, setError] = useState<string | null>(null);

  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setConfigText(e.target.value);
  };

  const handleSave = () => {
    try {
      const newConfig = JSON.parse(configText);

      // Validate the structure
      if (!newConfig.sse_servers || !Array.isArray(newConfig.sse_servers)) {
        throw new Error(t(I18nKey.SETTINGS$MCP_ERROR_SSE_ARRAY));
      }

      if (!newConfig.stdio_servers || !Array.isArray(newConfig.stdio_servers)) {
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
    }
  };

  return (
    <div>
      <div className="mb-2 text-sm text-gray-400">
        {t(I18nKey.SETTINGS$MCP_CONFIG_DESCRIPTION)}
      </div>
      <textarea
        className="w-full h-64 p-2 text-sm font-mono bg-base-tertiary rounded-md focus:border-blue-500 focus:outline-hidden"
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
      <div className="mt-4 flex justify-end">
        <BrandButton type="button" variant="primary" onClick={handleSave}>
          {t(I18nKey.SETTINGS$MCP_APPLY_CHANGES)}
        </BrandButton>
      </div>
    </div>
  );
}
