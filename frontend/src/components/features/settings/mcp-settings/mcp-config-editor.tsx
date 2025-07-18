import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { MCPConfig } from "#/types/settings";
import { I18nKey } from "#/i18n/declaration";
import { MCPSSEServers } from "./mcp-sse-servers";
import { MCPStdioServers } from "./mcp-stdio-servers";
import { MCPJsonEditor } from "./mcp-json-editor";
import { BrandButton } from "../brand-button";

interface MCPConfigEditorProps {
  mcpConfig?: MCPConfig;
  onChange: (config: MCPConfig) => void;
}

export function MCPConfigEditor({ mcpConfig, onChange }: MCPConfigEditorProps) {
  const { t } = useTranslation();
  const [isEditing, setIsEditing] = useState(false);
  const handleConfigChange = (newConfig: MCPConfig) => {
    onChange(newConfig);
    setIsEditing(false);
  };

  const config = mcpConfig || { sse_servers: [], stdio_servers: [] };

  return (
    <div>
      <div className="flex flex-col gap-2 mb-6">
        <div className="text-sm font-medium">
          {t(I18nKey.SETTINGS$MCP_TITLE)}
        </div>
        <p className="text-xs text-[#A3A3A3]">
          {t(I18nKey.SETTINGS$MCP_DESCRIPTION)}
        </p>
      </div>
      <div className="flex justify-between items-center mb-4">
        <div className="flex items-center">
          <a
            href="https://docs.all-hands.dev/usage/mcp"
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-blue-400 hover:underline mr-3"
            onClick={(e) => e.stopPropagation()}
          >
            {t(I18nKey.COMMON$DOCUMENTATION)}
          </a>
          <BrandButton
            type="button"
            variant="primary"
            onClick={() => setIsEditing(!isEditing)}
          >
            {isEditing
              ? t(I18nKey.SETTINGS$MCP_CANCEL)
              : t(I18nKey.SETTINGS$MCP_EDIT_CONFIGURATION)}
          </BrandButton>
        </div>
      </div>

      <div>
        {isEditing ? (
          <MCPJsonEditor mcpConfig={mcpConfig} onChange={handleConfigChange} />
        ) : (
          <>
            <div className="flex flex-col gap-6">
              <div>
                <MCPSSEServers servers={config.sse_servers} />
              </div>

              <div>
                <MCPStdioServers servers={config.stdio_servers} />
              </div>
            </div>

            {config.sse_servers.length === 0 &&
              config.stdio_servers.length === 0 && (
                <div className="mt-4 p-2 bg-yellow-50 border border-yellow-200 rounded-md text-sm text-yellow-700">
                  {t(I18nKey.SETTINGS$MCP_NO_SERVERS_CONFIGURED)}
                </div>
              )}
          </>
        )}
      </div>
    </div>
  );
}
