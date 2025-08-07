import React from "react";
import { useTranslation } from "react-i18next";
import { FaPencil, FaTrash } from "react-icons/fa6";
import { I18nKey } from "#/i18n/declaration";
import { MCPServerConfig } from "#/routes/mcp-settings";
import { MCPStdioServer, MCPSSEServer, MCPSHTTPServer } from "#/types/settings";

interface MCPServerListProps {
  servers: MCPServerConfig[];
  onEdit: (server: MCPServerConfig) => void;
  onDelete: (server: MCPServerConfig) => void;
}

export function MCPServerListSkeleton() {
  return (
    <div className="border-t border-[#717888] last-of-type:border-b max-w-[830px] pr-2.5 py-[13px] flex items-center justify-between">
      <div className="flex items-center justify-between w-1/3">
        <span className="skeleton h-4 w-1/2" />
        <span className="skeleton h-4 w-1/4" />
      </div>

      <div className="flex items-center gap-8">
        <span className="skeleton h-4 w-4" />
        <span className="skeleton h-4 w-4" />
      </div>
    </div>
  );
}

function MCPServerListItem({
  server,
  onEdit,
  onDelete,
}: {
  server: MCPServerConfig;
  onEdit: () => void;
  onDelete: () => void;
}) {
  const { t } = useTranslation();

  const getServerDisplayName = () => {
    if (server.type === "stdio") {
      return (server as MCPStdioServer).name;
    }
    return (server as MCPSSEServer | MCPSHTTPServer).url;
  };

  const getServerTypeLabel = () => {
    switch (server.type) {
      case "sse":
        return t(I18nKey.SETTINGS$MCP_SERVER_TYPE_SSE);
      case "stdio":
        return t(I18nKey.SETTINGS$MCP_SERVER_TYPE_STDIO);
      case "shttp":
        return t(I18nKey.SETTINGS$MCP_SERVER_TYPE_SHTTP);
      default:
        return server.type.toUpperCase();
    }
  };

  const getServerDescription = () => {
    if (server.type === "stdio") {
      const stdioServer = server as MCPStdioServer;
      return `${stdioServer.command}${stdioServer.args?.length ? ` ${stdioServer.args.join(" ")}` : ""}`;
    }

    const urlServer = server as MCPSSEServer | MCPSHTTPServer;
    return urlServer.api_key
      ? t(I18nKey.SETTINGS$MCP_API_KEY_CONFIGURED)
      : t(I18nKey.SETTINGS$MCP_NO_API_KEY);
  };

  return (
    <tr
      data-testid="mcp-server-item"
      className="flex w-full items-center border-t border-tertiary"
    >
      <td className="p-3 w-1/4 text-sm text-content-2">
        <div className="truncate" title={getServerDisplayName()}>
          {getServerDisplayName()}
        </div>
        <div className="text-xs text-content-3 mt-1">
          {getServerTypeLabel()}
        </div>
      </td>

      <td
        className="p-3 w-1/2 truncate overflow-hidden whitespace-nowrap text-sm text-content-2 opacity-80"
        title={getServerDescription()}
      >
        {getServerDescription()}
      </td>

      <td className="p-3 w-1/4 flex items-center justify-end gap-4">
        <button
          data-testid="edit-mcp-server-button"
          type="button"
          onClick={onEdit}
          aria-label={`Edit ${getServerDisplayName()}`}
          className="cursor-pointer hover:text-primary transition-colors"
        >
          <FaPencil size={16} />
        </button>
        <button
          data-testid="delete-mcp-server-button"
          type="button"
          onClick={onDelete}
          aria-label={`Delete ${getServerDisplayName()}`}
          className="cursor-pointer hover:text-red-500 transition-colors"
        >
          <FaTrash size={16} />
        </button>
      </td>
    </tr>
  );
}

export function MCPServerList({
  servers,
  onEdit,
  onDelete,
}: MCPServerListProps) {
  const { t } = useTranslation();

  if (servers.length === 0) {
    return (
      <div className="border border-tertiary rounded-md p-8 text-center">
        <p className="text-content-2 text-sm">
          {t(I18nKey.SETTINGS$MCP_NO_SERVERS_CONFIGURED)}
        </p>
        <p className="text-content-3 text-xs mt-2">
          {t(I18nKey.SETTINGS$MCP_ADD_SERVER_HINT)}
        </p>
      </div>
    );
  }

  return (
    <div className="border border-tertiary rounded-md overflow-hidden">
      <table className="w-full">
        <thead className="bg-base-tertiary">
          <tr className="flex w-full items-center">
            <th className="w-1/4 text-left p-3 text-sm font-medium">
              {t(I18nKey.SETTINGS$MCP_SERVER_NAME)}
            </th>
            <th className="w-1/2 text-left p-3 text-sm font-medium">
              {t(I18nKey.SETTINGS$MCP_SERVER_DETAILS)}
            </th>
            <th className="w-1/4 text-right p-3 text-sm font-medium">
              {t(I18nKey.SETTINGS$ACTIONS)}
            </th>
          </tr>
        </thead>
        <tbody>
          {servers.map((server) => (
            <MCPServerListItem
              key={server.id}
              server={server}
              onEdit={() => onEdit(server)}
              onDelete={() => onDelete(server)}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
}
