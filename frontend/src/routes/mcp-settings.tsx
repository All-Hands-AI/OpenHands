import React, { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import posthog from "posthog-js";
import { useSettings } from "#/hooks/query/use-settings";
import { useSaveSettings } from "#/hooks/mutation/use-save-settings";
import {
  MCPConfig,
  MCPSSEServer,
  MCPStdioServer,
  MCPSHTTPServer,
} from "#/types/settings";
import { BrandButton } from "#/components/features/settings/brand-button";
import { I18nKey } from "#/i18n/declaration";
import {
  displayErrorToast,
  displaySuccessToast,
} from "#/utils/custom-toast-handlers";
import { retrieveAxiosErrorMessage } from "#/utils/retrieve-axios-error-message";
import { MCPServerList } from "#/components/features/settings/mcp-settings/mcp-server-list";
import { MCPServerForm } from "#/components/features/settings/mcp-settings/mcp-server-form";
import { ConfirmationModal } from "#/components/shared/modals/confirmation-modal";

export type MCPServerType = "sse" | "stdio" | "shttp";

export type MCPServerConfig = {
  type: MCPServerType;
  id: string;
} & (MCPSSEServer | MCPStdioServer | MCPSHTTPServer);

function MCPSettingsScreen() {
  const { t } = useTranslation();
  const { data: settings, isLoading } = useSettings();
  const { mutate: saveSettings, isPending } = useSaveSettings();

  const [mcpConfig, setMcpConfig] = useState<MCPConfig>({
    sse_servers: [],
    stdio_servers: [],
    shttp_servers: [],
  });
  const [isDirty, setIsDirty] = useState(false);
  const [view, setView] = useState<
    "list" | "add-server-form" | "edit-server-form"
  >("list");
  const [selectedServer, setSelectedServer] = useState<MCPServerConfig | null>(
    null,
  );
  const [confirmationModalIsVisible, setConfirmationModalIsVisible] =
    useState(false);

  useEffect(() => {
    if (settings?.MCP_CONFIG) {
      setMcpConfig({
        sse_servers: settings.MCP_CONFIG.sse_servers || [],
        stdio_servers: settings.MCP_CONFIG.stdio_servers || [],
        shttp_servers: settings.MCP_CONFIG.shttp_servers || [],
      });
    }
  }, [settings]);

  const normalizeServer = (
    server: string | MCPSSEServer | MCPSHTTPServer,
  ): MCPSSEServer | MCPSHTTPServer => {
    if (typeof server === "string") {
      return { url: server };
    }
    return server;
  };

  const getAllServers = (): MCPServerConfig[] => {
    const servers: MCPServerConfig[] = [];

    mcpConfig.sse_servers.forEach((server, index) => {
      const normalizedServer = normalizeServer(server);
      servers.push({
        type: "sse",
        id: `sse-${index}`,
        ...normalizedServer,
      } as MCPServerConfig);
    });

    mcpConfig.stdio_servers.forEach((server, index) => {
      servers.push({
        type: "stdio",
        id: `stdio-${index}`,
        ...server,
      } as MCPServerConfig);
    });

    mcpConfig.shttp_servers.forEach((server, index) => {
      const normalizedServer = normalizeServer(server);
      servers.push({
        type: "shttp",
        id: `shttp-${index}`,
        ...normalizedServer,
      } as MCPServerConfig);
    });

    return servers;
  };

  const handleAddServer = (serverConfig: Omit<MCPServerConfig, "id">) => {
    const newConfig = { ...mcpConfig };

    if (serverConfig.type === "sse") {
      const { type, ...server } = serverConfig;
      newConfig.sse_servers = [
        ...newConfig.sse_servers,
        server as MCPSSEServer,
      ];
    } else if (serverConfig.type === "stdio") {
      const { type, ...server } = serverConfig;
      newConfig.stdio_servers = [
        ...newConfig.stdio_servers,
        server as MCPStdioServer,
      ];
    } else if (serverConfig.type === "shttp") {
      const { type, ...server } = serverConfig;
      newConfig.shttp_servers = [
        ...newConfig.shttp_servers,
        server as MCPSHTTPServer,
      ];
    }

    setMcpConfig(newConfig);
    setIsDirty(true);
    setView("list");
  };

  const handleEditServer = (serverConfig: MCPServerConfig) => {
    const newConfig = { ...mcpConfig };
    const [, indexStr] = serverConfig.id.split("-");
    const index = parseInt(indexStr, 10);

    if (serverConfig.type === "sse") {
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      const { type, id, ...server } = serverConfig;
      newConfig.sse_servers[index] = server as MCPSSEServer;
    } else if (serverConfig.type === "stdio") {
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      const { type, id, ...server } = serverConfig;
      newConfig.stdio_servers[index] = server as MCPStdioServer;
    } else if (serverConfig.type === "shttp") {
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      const { type, id, ...server } = serverConfig;
      newConfig.shttp_servers[index] = server as MCPSHTTPServer;
    }

    setMcpConfig(newConfig);
    setIsDirty(true);
    setView("list");
  };

  const handleDeleteServer = (serverId: string) => {
    const newConfig = { ...mcpConfig };
    const [serverType, indexStr] = serverId.split("-");
    const index = parseInt(indexStr, 10);

    if (serverType === "sse") {
      newConfig.sse_servers.splice(index, 1);
    } else if (serverType === "stdio") {
      newConfig.stdio_servers.splice(index, 1);
    } else if (serverType === "shttp") {
      newConfig.shttp_servers.splice(index, 1);
    }

    setMcpConfig(newConfig);
    setIsDirty(true);
    setConfirmationModalIsVisible(false);
  };

  const handleSaveSettings = () => {
    if (!settings) return;

    saveSettings(
      { MCP_CONFIG: mcpConfig },
      {
        onSuccess: () => {
          displaySuccessToast(t(I18nKey.SETTINGS$SAVED));
          posthog.capture("settings_saved", {
            HAS_MCP_CONFIG: true,
            MCP_SSE_SERVERS_COUNT: mcpConfig.sse_servers.length,
            MCP_STDIO_SERVERS_COUNT: mcpConfig.stdio_servers.length,
            MCP_SHTTP_SERVERS_COUNT: mcpConfig.shttp_servers.length,
          });
          setIsDirty(false);
        },
        onError: (error) => {
          const errorMessage = retrieveAxiosErrorMessage(error);
          displayErrorToast(errorMessage || t(I18nKey.ERROR$GENERIC));
        },
      },
    );
  };

  if (isLoading) {
    return <div className="p-9">{t(I18nKey.HOME$LOADING)}</div>;
  }

  const allServers = getAllServers();

  return (
    <div
      data-testid="mcp-settings-screen"
      className="px-11 py-9 flex flex-col gap-5"
    >
      <div className="flex flex-col gap-2 mb-6">
        <div className="text-sm font-medium">
          {t(I18nKey.SETTINGS$MCP_TITLE)}
        </div>
        <p className="text-xs text-[#A3A3A3]">
          {t(I18nKey.SETTINGS$MCP_DESCRIPTION)}
        </p>
      </div>

      {view === "list" && (
        <BrandButton
          testId="add-mcp-server-button"
          type="button"
          variant="primary"
          onClick={() => setView("add-server-form")}
        >
          {t(I18nKey.SETTINGS$MCP_ADD_SERVER)}
        </BrandButton>
      )}

      {view === "list" && (
        <MCPServerList
          servers={allServers}
          onEdit={(server) => {
            setSelectedServer(server);
            setView("edit-server-form");
          }}
          onDelete={(server) => {
            setSelectedServer(server);
            setConfirmationModalIsVisible(true);
          }}
        />
      )}

      {(view === "add-server-form" || view === "edit-server-form") && (
        <MCPServerForm
          mode={view === "add-server-form" ? "add" : "edit"}
          server={selectedServer}
          onSave={
            view === "add-server-form" ? handleAddServer : handleEditServer
          }
          onCancel={() => {
            setView("list");
            setSelectedServer(null);
          }}
        />
      )}

      {isDirty && view === "list" && (
        <div className="flex gap-6 justify-end border-t border-t-tertiary pt-6">
          <BrandButton
            testId="save-mcp-settings-button"
            type="button"
            variant="primary"
            onClick={handleSaveSettings}
            isDisabled={isPending}
          >
            {!isPending && t(I18nKey.SETTINGS$SAVE_CHANGES)}
            {isPending && t(I18nKey.SETTINGS$SAVING)}
          </BrandButton>
        </div>
      )}

      {confirmationModalIsVisible && selectedServer && (
        <ConfirmationModal
          text={t(I18nKey.SETTINGS$MCP_CONFIRM_DELETE_SERVER, {
            serverName:
              selectedServer.type === "stdio"
                ? (selectedServer as MCPStdioServer).name
                : (selectedServer as MCPSSEServer | MCPSHTTPServer).url,
          })}
          onConfirm={() => handleDeleteServer(selectedServer.id)}
          onCancel={() => setConfirmationModalIsVisible(false)}
        />
      )}
    </div>
  );
}

export default MCPSettingsScreen;
