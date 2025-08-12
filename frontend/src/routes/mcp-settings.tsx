import React from "react";
import { useTranslation } from "react-i18next";
import { useSettings } from "#/hooks/query/use-settings";
import { useSaveSettings } from "#/hooks/mutation/use-save-settings";
import { I18nKey } from "#/i18n/declaration";

import { MCPServerList } from "#/components/features/settings/mcp-settings/mcp-server-list";
import { MCPServerForm } from "#/components/features/settings/mcp-settings/mcp-server-form";
import { ConfirmationModal } from "#/components/shared/modals/confirmation-modal";
import { BrandButton } from "#/components/features/settings/brand-button";
import {
  MCPConfig,
  MCPSSEServer,
  MCPStdioServer,
  MCPSHTTPServer,
} from "#/types/settings";

type MCPServerType = "sse" | "stdio" | "shttp";

interface MCPServerConfig {
  id: string;
  type: MCPServerType;
  name?: string;
  url?: string;
  api_key?: string;
  command?: string;
  args?: string[];
  env?: Record<string, string>;
}

function MCPSettingsScreen() {
  const { t } = useTranslation();
  const { data: settings, isLoading } = useSettings();
  const { mutate: saveSettings } = useSaveSettings();

  const [view, setView] = React.useState<"list" | "add" | "edit">("list");
  const [editingServer, setEditingServer] =
    React.useState<MCPServerConfig | null>(null);
  const [confirmationModalIsVisible, setConfirmationModalIsVisible] =
    React.useState(false);
  const [serverToDelete, setServerToDelete] = React.useState<string | null>(
    null,
  );
  const [isDirty, setIsDirty] = React.useState(false);

  const mcpConfig: MCPConfig = settings?.MCP_CONFIG || {
    sse_servers: [],
    stdio_servers: [],
    shttp_servers: [],
  };

  const [localMcpConfig, setMcpConfig] = React.useState<MCPConfig>(mcpConfig);

  React.useEffect(() => {
    if (settings?.MCP_CONFIG) {
      setMcpConfig(settings.MCP_CONFIG);
    }
  }, [settings?.MCP_CONFIG]);

  // Convert servers to a unified format for display
  const allServers: MCPServerConfig[] = [
    ...localMcpConfig.sse_servers.map((server, index) => ({
      id: `sse-${index}`,
      type: "sse" as const,
      url: typeof server === "string" ? server : server.url,
      api_key: typeof server === "object" ? server.api_key : undefined,
    })),
    ...localMcpConfig.stdio_servers.map((server, index) => ({
      id: `stdio-${index}`,
      type: "stdio" as const,
      name: server.name,
      command: server.command,
      args: server.args,
      env: server.env,
    })),
    ...localMcpConfig.shttp_servers.map((server, index) => ({
      id: `shttp-${index}`,
      type: "shttp" as const,
      url: typeof server === "string" ? server : server.url,
      api_key: typeof server === "object" ? server.api_key : undefined,
    })),
  ];

  const handleAddServer = (serverConfig: MCPServerConfig) => {
    const newConfig = { ...localMcpConfig };

    if (serverConfig.type === "sse") {
      const server: MCPSSEServer = {
        url: serverConfig.url!,
        ...(serverConfig.api_key && { api_key: serverConfig.api_key }),
      };
      newConfig.sse_servers.push(server);
    } else if (serverConfig.type === "stdio") {
      const server: MCPStdioServer = {
        name: serverConfig.name!,
        command: serverConfig.command!,
        ...(serverConfig.args && { args: serverConfig.args }),
        ...(serverConfig.env && { env: serverConfig.env }),
      };
      newConfig.stdio_servers.push(server);
    } else if (serverConfig.type === "shttp") {
      const server: MCPSHTTPServer = {
        url: serverConfig.url!,
        ...(serverConfig.api_key && { api_key: serverConfig.api_key }),
      };
      newConfig.shttp_servers.push(server);
    }

    setMcpConfig(newConfig);
    setIsDirty(true);
    setView("list");
  };

  const handleEditServer = (serverConfig: MCPServerConfig) => {
    const newConfig = { ...localMcpConfig };
    const [, indexStr] = serverConfig.id.split("-");
    const index = parseInt(indexStr, 10);

    if (serverConfig.type === "sse") {
      const server: MCPSSEServer = {
        url: serverConfig.url!,
        ...(serverConfig.api_key && { api_key: serverConfig.api_key }),
      };
      newConfig.sse_servers[index] = server;
    } else if (serverConfig.type === "stdio") {
      const server: MCPStdioServer = {
        name: serverConfig.name!,
        command: serverConfig.command!,
        ...(serverConfig.args && { args: serverConfig.args }),
        ...(serverConfig.env && { env: serverConfig.env }),
      };
      newConfig.stdio_servers[index] = server;
    } else if (serverConfig.type === "shttp") {
      const server: MCPSHTTPServer = {
        url: serverConfig.url!,
        ...(serverConfig.api_key && { api_key: serverConfig.api_key }),
      };
      newConfig.shttp_servers[index] = server;
    }

    setMcpConfig(newConfig);
    setIsDirty(true);
    setView("list");
  };

  const handleDeleteServer = (serverId: string) => {
    setMcpConfig((prevConfig) => {
      const newConfig = { ...prevConfig };
      const [serverType, indexStr] = serverId.split("-");
      const index = parseInt(indexStr, 10);

      if (serverType === "sse") {
        newConfig.sse_servers.splice(index, 1);
      } else if (serverType === "stdio") {
        newConfig.stdio_servers.splice(index, 1);
      } else if (serverType === "shttp") {
        newConfig.shttp_servers.splice(index, 1);
      }

      return newConfig;
    });

    setConfirmationModalIsVisible(false);
    setIsDirty(true);
  };

  const handleSaveSettings = () => {
    if (!settings) return;

    const updatedSettings = {
      ...settings,
      MCP_CONFIG: localMcpConfig,
    };

    saveSettings(updatedSettings, {
      onSuccess: () => {
        setIsDirty(false);
      },
    });
  };

  const handleEditClick = (server: MCPServerConfig) => {
    setEditingServer(server);
    setView("edit");
  };

  const handleDeleteClick = (serverId: string) => {
    setServerToDelete(serverId);
    setConfirmationModalIsVisible(true);
  };

  const handleConfirmDelete = () => {
    if (serverToDelete) {
      handleDeleteServer(serverToDelete);
      setServerToDelete(null);
    }
  };

  const handleCancelDelete = () => {
    setConfirmationModalIsVisible(false);
    setServerToDelete(null);
  };

  if (isLoading) {
    return (
      <div className="px-11 py-9 flex flex-col gap-5">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-300 rounded w-1/4 mb-4" />
          <div className="h-4 bg-gray-300 rounded w-1/2 mb-8" />
          <div className="h-10 bg-gray-300 rounded w-32" />
        </div>
      </div>
    );
  }

  return (
    <div className="px-11 py-9 flex flex-col gap-5">
      {view === "list" && (
        <>
          <BrandButton
            testId="add-mcp-server-button"
            type="button"
            variant="primary"
            onClick={() => setView("add")}
            isDisabled={isLoading}
          >
            {t(I18nKey.SETTINGS$MCP_ADD_SERVER)}
          </BrandButton>

          <MCPServerList
            servers={allServers}
            onEdit={handleEditClick}
            onDelete={handleDeleteClick}
          />

          {isDirty && (
            <div className="flex justify-end">
              <BrandButton
                testId="save-mcp-settings-button"
                type="button"
                variant="primary"
                onClick={handleSaveSettings}
              >
                {t(I18nKey.SETTINGS$SAVE_CHANGES)}
              </BrandButton>
            </div>
          )}
        </>
      )}

      {view === "add" && (
        <MCPServerForm
          mode="add"
          existingServers={allServers}
          onSubmit={handleAddServer}
          onCancel={() => setView("list")}
        />
      )}

      {view === "edit" && editingServer && (
        <MCPServerForm
          mode="edit"
          server={editingServer}
          existingServers={allServers}
          onSubmit={handleEditServer}
          onCancel={() => {
            setView("list");
            setEditingServer(null);
          }}
        />
      )}

      {confirmationModalIsVisible && (
        <ConfirmationModal
          text={t(I18nKey.SETTINGS$MCP_CONFIRM_DELETE)}
          onConfirm={handleConfirmDelete}
          onCancel={handleCancelDelete}
        />
      )}
    </div>
  );
}

export default MCPSettingsScreen;
