import React from "react";
import { MCPConfig, MCPSSEServer, MCPStdioServer } from "#/types/settings";

interface MCPConfigViewerProps {
  mcpConfig?: MCPConfig;
}

export function MCPConfigViewer({ mcpConfig }: MCPConfigViewerProps) {
  const [isExpanded, setIsExpanded] = React.useState(false);

  if (
    !mcpConfig ||
    (mcpConfig.sse_servers.length === 0 && mcpConfig.stdio_servers.length === 0)
  ) {
    return null;
  }

  const toggleExpand = () => {
    setIsExpanded(!isExpanded);
  };

  const renderSSEServer = (server: string | MCPSSEServer, index: number) => {
    if (typeof server === "string") {
      return (
        <div
          key={`sse-${index}`}
          className="mb-2 p-2 bg-base-tertiary rounded-md"
        >
          <div className="text-sm font-medium">URL: {server}</div>
        </div>
      );
    }
    return (
      <div
        key={`sse-${index}`}
        className="mb-2 p-2 bg-base-tertiary rounded-md"
      >
        <div className="text-sm font-medium">URL: {server.url}</div>
        {server.api_key && (
          <div className="text-xs text-gray-400">
            API Key: {server.api_key ? "Set" : "Not set"}
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
      <div className="text-sm font-medium">Name: {server.name}</div>
      <div className="text-xs">Command: {server.command}</div>
      {server.args && server.args.length > 0 && (
        <div className="text-xs">Args: {server.args.join(" ")}</div>
      )}
      {server.env && Object.keys(server.env).length > 0 && (
        <div className="text-xs">
          Env:{" "}
          {Object.entries(server.env)
            .map(([key, value]) => `${key}=${value}`)
            .join(", ")}
        </div>
      )}
    </div>
  );

  return (
    <div className="mt-4 border border-base-tertiary rounded-md p-3">
      <div className="flex justify-between items-center">
        <div
          className="flex items-center cursor-pointer"
          onClick={toggleExpand}
        >
          <h3 className="text-sm font-medium">MCP Configuration</h3>
          <button type="button" className="ml-2 text-xs text-gray-400">
            {isExpanded ? "Hide" : "Show"}
          </button>
        </div>
        <a
          href="https://docs.all-hands.dev/modules/usage/mcp"
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs text-blue-400 hover:underline"
          onClick={(e) => e.stopPropagation()}
        >
          Learn more
        </a>
      </div>

      {isExpanded && (
        <div className="mt-2">
          {mcpConfig.sse_servers.length > 0 && (
            <div className="mb-3">
              <h4 className="text-xs font-medium mb-1">SSE Servers</h4>
              {mcpConfig.sse_servers.map(renderSSEServer)}
            </div>
          )}

          {mcpConfig.stdio_servers.length > 0 && (
            <div>
              <h4 className="text-xs font-medium mb-1">Stdio Servers</h4>
              {mcpConfig.stdio_servers.map(renderStdioServer)}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
