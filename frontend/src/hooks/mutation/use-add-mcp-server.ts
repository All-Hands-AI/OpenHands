import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useSettings } from "#/hooks/query/use-settings";
import OpenHands from "#/api/open-hands";
import { MCPSSEServer, MCPStdioServer, MCPSHTTPServer } from "#/types/settings";

type MCPServerType = "sse" | "stdio" | "shttp";

interface MCPServerConfig {
  type: MCPServerType;
  name?: string;
  url?: string;
  api_key?: string;
  command?: string;
  args?: string[];
  env?: Record<string, string>;
}

export function useAddMcpServer() {
  const queryClient = useQueryClient();
  const { data: settings } = useSettings();

  return useMutation({
    mutationFn: async (server: MCPServerConfig): Promise<void> => {
      if (!settings) return;

      const currentConfig = settings.MCP_CONFIG || {
        sse_servers: [],
        stdio_servers: [],
        shttp_servers: [],
      };

      const newConfig = { ...currentConfig };

      if (server.type === "sse") {
        const sseServer: MCPSSEServer = {
          url: server.url!,
          ...(server.api_key && { api_key: server.api_key }),
        };
        newConfig.sse_servers.push(sseServer);
      } else if (server.type === "stdio") {
        const stdioServer: MCPStdioServer = {
          name: server.name!,
          command: server.command!,
          ...(server.args && { args: server.args }),
          ...(server.env && { env: server.env }),
        };
        newConfig.stdio_servers.push(stdioServer);
      } else if (server.type === "shttp") {
        const shttpServer: MCPSHTTPServer = {
          url: server.url!,
          ...(server.api_key && { api_key: server.api_key }),
        };
        newConfig.shttp_servers.push(shttpServer);
      }

      const apiSettings = {
        mcp_config: newConfig,
      };

      await OpenHands.saveSettings(apiSettings);
    },
    onSuccess: () => {
      // Invalidate the settings query to trigger a refetch
      queryClient.invalidateQueries({ queryKey: ["settings"] });
    },
  });
}
