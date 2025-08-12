import { FaPencil, FaTrash } from "react-icons/fa6";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";

interface MCPServerConfig {
  id: string;
  type: "sse" | "stdio" | "shttp";
  name?: string;
  url?: string;
  api_key?: string;
  command?: string;
  args?: string[];
  env?: Record<string, string>;
}

interface MCPServerListProps {
  servers: MCPServerConfig[];
  onEdit: (server: MCPServerConfig) => void;
  onDelete: (serverId: string) => void;
}

function MCPServerListItemSkeleton() {
  return (
    <tr className="grid grid-cols-[25%_120px_1fr_120px] gap-4 items-start border-t border-tertiary">
      <td className="p-3" aria-label="Name loading">
        <div className="skeleton h-4 w-3/4" />
      </td>
      <td className="p-3" aria-label="Type loading">
        <div className="skeleton h-4 w-16" />
      </td>
      <td className="p-3" aria-label="Details loading">
        <div className="skeleton h-4 w-full" />
      </td>
      <td
        className="p-3 flex items-center justify-end gap-4"
        aria-label="Actions loading"
      >
        <div className="skeleton h-4 w-4" />
        <div className="skeleton h-4 w-4" />
      </td>
    </tr>
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

  const getServerTypeLabel = (type: string) => {
    switch (type) {
      case "sse":
        return t(I18nKey.SETTINGS$MCP_SERVER_TYPE_SSE);
      case "stdio":
        return t(I18nKey.SETTINGS$MCP_SERVER_TYPE_STDIO);
      case "shttp":
        return t(I18nKey.SETTINGS$MCP_SERVER_TYPE_SHTTP);
      default:
        return type.toUpperCase();
    }
  };

  const getServerDescription = (serverConfig: MCPServerConfig) => {
    if (serverConfig.type === "stdio") {
      if (serverConfig.command) {
        const args =
          serverConfig.args && serverConfig.args.length > 0
            ? ` ${serverConfig.args.join(" ")}`
            : "";
        return `${serverConfig.command}${args}`;
      }
      return serverConfig.name || "";
    }
    if (
      (serverConfig.type === "sse" || serverConfig.type === "shttp") &&
      serverConfig.url
    ) {
      return serverConfig.url;
    }
    return "";
  };

  const serverName = server.type === "stdio" ? server.name : server.url;
  const serverDescription = getServerDescription(server);

  return (
    <tr
      data-testid="mcp-server-item"
      className="grid grid-cols-[25%_120px_1fr_120px] gap-4 items-start border-t border-tertiary"
    >
      <td
        className="p-3 text-sm text-content-2 truncate min-w-0"
        title={serverName}
      >
        {serverName}
      </td>

      <td className="p-3 text-sm text-content-2 whitespace-nowrap">
        {getServerTypeLabel(server.type)}
      </td>

      <td
        className="p-3 text-sm text-content-2 opacity-80 italic min-w-0 break-all"
        title={serverDescription}
      >
        {serverDescription}
      </td>

      <td className="p-3 flex items-start justify-end gap-4 whitespace-nowrap">
        <button
          data-testid="edit-mcp-server-button"
          type="button"
          onClick={onEdit}
          aria-label={`Edit ${serverName}`}
          className="cursor-pointer hover:text-content-1 transition-colors"
        >
          <FaPencil size={16} />
        </button>
        <button
          data-testid="delete-mcp-server-button"
          type="button"
          onClick={onDelete}
          aria-label={`Delete ${serverName}`}
          className="cursor-pointer hover:text-content-1 transition-colors"
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
          {t(I18nKey.SETTINGS$MCP_NO_SERVERS)}
        </p>
      </div>
    );
  }

  return (
    <div className="border border-tertiary rounded-md overflow-hidden">
      <table className="w-full">
        <thead className="bg-base-tertiary">
          <tr className="grid grid-cols-[25%_120px_1fr_120px] gap-4 items-start">
            <th className="text-left p-3 text-sm font-medium">
              {t(I18nKey.SETTINGS$NAME)}
            </th>
            <th className="text-left p-3 text-sm font-medium">
              {t(I18nKey.SETTINGS$MCP_SERVER_TYPE)}
            </th>
            <th className="text-left p-3 text-sm font-medium">
              {t(I18nKey.SETTINGS$MCP_SERVER_DETAILS)}
            </th>
            <th className="text-right p-3 text-sm font-medium">
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
              onDelete={() => onDelete(server.id)}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
}

export { MCPServerListItemSkeleton };
