import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { MCPConfig, MCPSSEServer, MCPStdioServer } from "#/types/settings";

interface MCPConfigEditorProps {
  mcpConfig?: MCPConfig;
  onChange: (config: MCPConfig) => void;
}

export function MCPConfigEditor({ mcpConfig, onChange }: MCPConfigEditorProps) {
  const { t } = useTranslation();
  const [isExpanded, setIsExpanded] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [configText, setConfigText] = useState(() => {
    return mcpConfig ? JSON.stringify(mcpConfig, null, 2) : "{\n  \"sse_servers\": [],\n  \"stdio_servers\": []\n}";
  });
  const [error, setError] = useState<string | null>(null);

  const toggleExpand = () => {
    setIsExpanded(!isExpanded);
  };

  const toggleEdit = () => {
    if (isEditing) {
      // Save changes
      try {
        const newConfig = JSON.parse(configText);
        
        // Validate the structure
        if (!newConfig.sse_servers || !Array.isArray(newConfig.sse_servers)) {
          throw new Error("sse_servers must be an array");
        }
        
        if (!newConfig.stdio_servers || !Array.isArray(newConfig.stdio_servers)) {
          throw new Error("stdio_servers must be an array");
        }
        
        // Validate SSE servers
        for (const server of newConfig.sse_servers) {
          if (typeof server !== "string" && (!server.url || typeof server.url !== "string")) {
            throw new Error("Each SSE server must be a string URL or have a url property");
          }
        }
        
        // Validate stdio servers
        for (const server of newConfig.stdio_servers) {
          if (!server.name || !server.command) {
            throw new Error("Each stdio server must have name and command properties");
          }
        }
        
        onChange(newConfig);
        setError(null);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Invalid JSON");
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
        <div key={`sse-${index}`} className="mb-2 p-2 bg-base-tertiary rounded-md border border-gray-200">
          <div className="text-xs font-medium flex items-center">
            <span className="bg-blue-100 text-blue-800 text-xs px-1.5 py-0.5 rounded mr-2">SSE</span>
            {server}
          </div>
        </div>
      );
    } else {
      return (
        <div key={`sse-${index}`} className="mb-2 p-2 bg-base-tertiary rounded-md border border-gray-200">
          <div className="text-xs font-medium flex items-center">
            <span className="bg-blue-100 text-blue-800 text-xs px-1.5 py-0.5 rounded mr-2">SSE</span>
            {server.url}
          </div>
          {server.api_key && (
            <div className="mt-1 text-xs text-gray-500 flex items-center">
              <span className="bg-green-100 text-green-800 text-xs px-1.5 py-0.5 rounded mr-2">API Key</span>
              <span>{server.api_key ? "Configured" : "Not set"}</span>
            </div>
          )}
        </div>
      );
    }
  };

  const renderStdioServer = (server: MCPStdioServer, index: number) => {
    return (
      <div key={`stdio-${index}`} className="mb-2 p-2 bg-base-tertiary rounded-md border border-gray-200">
        <div className="text-xs font-medium flex items-center">
          <span className="bg-purple-100 text-purple-800 text-xs px-1.5 py-0.5 rounded mr-2">STDIO</span>
          {server.name}
        </div>
        <div className="mt-1 text-xs text-gray-500 flex items-center">
          <span className="bg-gray-100 text-gray-800 text-xs px-1.5 py-0.5 rounded mr-2">Command</span>
          <code className="font-mono">{server.command}</code>
        </div>
        {server.args && server.args.length > 0 && (
          <div className="mt-1 text-xs text-gray-500 flex items-center">
            <span className="bg-gray-100 text-gray-800 text-xs px-1.5 py-0.5 rounded mr-2">Args</span>
            <code className="font-mono">{server.args.join(" ")}</code>
          </div>
        )}
        {server.env && Object.keys(server.env).length > 0 && (
          <div className="mt-1 text-xs text-gray-500 flex items-center">
            <span className="bg-gray-100 text-gray-800 text-xs px-1.5 py-0.5 rounded mr-2">Env</span>
            <code className="font-mono">
              {Object.entries(server.env)
                .map(([key, value]) => `${key}=${value}`)
                .join(", ")}
            </code>
          </div>
        )}
      </div>
    );
  };

  const config = mcpConfig || { sse_servers: [], stdio_servers: [] };

  return (
    <div className="border border-base-tertiary rounded-md p-3">
      <div className="flex justify-between items-center">
        <div 
          className="flex items-center cursor-pointer" 
          onClick={toggleExpand}
        >
          <button className="text-xs bg-base-tertiary px-2 py-1 rounded-md">
            {isExpanded ? "Hide Details" : "Show Details"}
          </button>
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
            className="text-xs bg-blue-500 text-white px-2 py-1 rounded-md hover:bg-blue-600"
            onClick={toggleEdit}
          >
            {isEditing ? "Save Changes" : "Edit Configuration"}
          </button>
        </div>
      </div>
      
      {isExpanded && (
        <div className="mt-2">
          {isEditing ? (
            <div>
              <div className="mb-2 text-xs text-gray-400">
                Edit the JSON configuration for MCP servers below. The configuration must include both <code>sse_servers</code> and <code>stdio_servers</code> arrays.
              </div>
              <textarea 
                className="w-full h-64 p-2 text-xs font-mono bg-base-tertiary rounded-md border border-base-tertiary focus:border-blue-500 focus:outline-none"
                value={configText}
                onChange={handleTextChange}
                spellCheck="false"
              />
              {error && (
                <div className="mt-2 p-2 bg-red-100 border border-red-300 rounded-md text-xs text-red-700">
                  <strong>Error:</strong> {error}
                </div>
              )}
              <div className="mt-2 text-xs text-gray-400">
                <strong>Example:</strong> <code>{"{ \"sse_servers\": [\"https://example.com/mcp\"], \"stdio_servers\": [{ \"name\": \"example\", \"command\": \"python\", \"args\": [\"-m\", \"mcp_server\"] }] }"}</code>
              </div>
            </div>
          ) : (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="mb-3">
                  <h4 className="text-xs font-medium mb-1 flex items-center">
                    <span className="mr-1">SSE Servers</span>
                    <span className="bg-gray-200 text-gray-700 text-xs px-1.5 py-0.5 rounded-full">
                      {config.sse_servers.length}
                    </span>
                  </h4>
                  {config.sse_servers.length > 0 ? (
                    config.sse_servers.map(renderSSEServer)
                  ) : (
                    <div className="p-2 bg-base-tertiary rounded-md text-xs text-gray-400">
                      No SSE servers configured
                    </div>
                  )}
                </div>
                
                <div>
                  <h4 className="text-xs font-medium mb-1 flex items-center">
                    <span className="mr-1">Stdio Servers</span>
                    <span className="bg-gray-200 text-gray-700 text-xs px-1.5 py-0.5 rounded-full">
                      {config.stdio_servers.length}
                    </span>
                  </h4>
                  {config.stdio_servers.length > 0 ? (
                    config.stdio_servers.map(renderStdioServer)
                  ) : (
                    <div className="p-2 bg-base-tertiary rounded-md text-xs text-gray-400">
                      No stdio servers configured
                    </div>
                  )}
                </div>
              </div>
              
              {config.sse_servers.length === 0 && config.stdio_servers.length === 0 && (
                <div className="mt-2 p-2 bg-yellow-50 border border-yellow-200 rounded-md text-xs text-yellow-700">
                  No MCP servers are currently configured. Click "Edit Configuration" to add servers.
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}