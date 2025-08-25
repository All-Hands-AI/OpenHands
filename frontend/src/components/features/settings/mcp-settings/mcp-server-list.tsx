import { useTranslation } from "react-i18next";
import { MCPServerListItem } from "./mcp-server-list-item";
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
          <tr className="grid grid-cols-[minmax(0,0.25fr)_120px_minmax(0,1fr)_120px] gap-4 items-start">
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
