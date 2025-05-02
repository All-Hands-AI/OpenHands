import { useTranslation } from "react-i18next";
import { useState } from "react";
import posthog from "posthog-js";
import { useSettings } from "#/hooks/query/use-settings";
import { useSaveSettings } from "#/hooks/mutation/use-save-settings";
import { MCPConfig } from "#/types/settings";
import { MCPConfigEditor } from "#/components/features/settings/mcp-settings/mcp-config-editor";
import { BrandButton } from "#/components/features/settings/brand-button";
import { I18nKey } from "#/i18n/declaration";
import {
  displayErrorToast,
  displaySuccessToast,
} from "#/utils/custom-toast-handlers";
import { retrieveAxiosErrorMessage } from "#/utils/retrieve-axios-error-message";

function MCPSettings() {
  const { data: settings, isLoading } = useSettings();
  const { mutate: saveSettings, isPending } = useSaveSettings();
  const { t } = useTranslation();

  const [mcpConfig, setMcpConfig] = useState<MCPConfig | undefined>(
    settings?.MCP_CONFIG,
  );
  const [isDirty, setIsDirty] = useState(false);

  const handleConfigChange = (config: MCPConfig) => {
    setMcpConfig(config);
    setIsDirty(true);
  };

  const formAction = () => {
    if (!settings) return;

    const newSettings = {
      ...settings,
      MCP_CONFIG: mcpConfig,
    };

    saveSettings(newSettings, {
      onSuccess: () => {
        displaySuccessToast(t(I18nKey.SETTINGS$SAVED));
        posthog.capture("settings_saved", {
          HAS_MCP_CONFIG: newSettings.MCP_CONFIG ? "YES" : "NO",
          MCP_SSE_SERVERS_COUNT:
            newSettings.MCP_CONFIG?.sse_servers?.length || 0,
          MCP_STDIO_SERVERS_COUNT:
            newSettings.MCP_CONFIG?.stdio_servers?.length || 0,
        });
        setIsDirty(false);
      },
      onError: (error) => {
        const errorMessage = retrieveAxiosErrorMessage(error);
        displayErrorToast(errorMessage || t(I18nKey.ERROR$GENERIC));
      },
    });
  };

  if (isLoading) {
    return <div className="p-9">Loading...</div>;
  }

  return (
    <form
      data-testid="mcp-settings-screen"
      action={formAction}
      className="flex flex-col h-full justify-between"
    >
      <div className="p-9 flex flex-col gap-6">
        <div>
          <h2 className="text-lg font-medium mb-2">
            {t("SETTINGS$MCP_TITLE")}
          </h2>
          <p className="text-sm text-gray-400 mb-4">
            {t("SETTINGS$MCP_DESCRIPTION")}
          </p>
        </div>

        <MCPConfigEditor mcpConfig={mcpConfig} onChange={handleConfigChange} />
      </div>

      <div className="flex gap-6 p-6 justify-end border-t border-t-tertiary">
        <BrandButton
          testId="submit-button"
          type="submit"
          variant="primary"
          isDisabled={!isDirty || isPending}
        >
          {!isPending && t("SETTINGS$SAVE_CHANGES")}
          {isPending && t("SETTINGS$SAVING")}
        </BrandButton>
      </div>
    </form>
  );
}

export default MCPSettings;
