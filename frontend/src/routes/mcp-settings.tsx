import { useTranslation } from "react-i18next";
import { useState } from "react";
import posthog from "posthog-js";
import { useSettings } from "#/hooks/query/use-settings";
import { useSaveSettings } from "#/hooks/mutation/use-save-settings";
import { MCPConfig } from "#/types/settings";
import { MCPConfigEditor } from "#/components/features/settings/mcp-settings/mcp-config-editor";
import { BrandButton } from "#/components/features/settings/brand-button";
import { I18nKey } from "#/i18n/declaration";

function MCPSettings() {
  const { data: settings, isLoading } = useSettings();
  const { mutate: saveSettings } = useSaveSettings();
  const { t } = useTranslation();

  const [mcpConfig, setMcpConfig] = useState<MCPConfig | undefined>(
    settings?.MCP_CONFIG,
  );

  const handleSave = () => {
    if (!settings) return;

    const newSettings = {
      ...settings,
      MCP_CONFIG: mcpConfig,
    };

    saveSettings(newSettings, {
      onSuccess: () => {
        posthog.capture("settings_saved", {
          HAS_MCP_CONFIG: newSettings.MCP_CONFIG ? "YES" : "NO",
          MCP_SSE_SERVERS_COUNT:
            newSettings.MCP_CONFIG?.sse_servers?.length || 0,
          MCP_STDIO_SERVERS_COUNT:
            newSettings.MCP_CONFIG?.stdio_servers?.length || 0,
        });
      },
    });
  };

  if (isLoading) {
    return <div className="p-6">Loading...</div>;
  }

  return (
    <div className="p-6 flex flex-col gap-6">
      <div>
        <h2 className="text-lg font-medium mb-2">{t("SETTINGS$MCP_TITLE")}</h2>
        <p className="text-sm text-gray-400 mb-4">
          {t("SETTINGS$MCP_DESCRIPTION")}
        </p>
      </div>

      <MCPConfigEditor mcpConfig={mcpConfig} onChange={setMcpConfig} />

      <div className="flex justify-end">
        <BrandButton
          type="button"
          variant="primary"
          onClick={handleSave}
          className="w-32"
        >
          {t(I18nKey.BUTTON$SAVE)}
        </BrandButton>
      </div>
    </div>
  );
}

export default MCPSettings;
