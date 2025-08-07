import React, { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { MCPServerConfig, MCPServerType } from "#/routes/mcp-settings";
import { MCPStdioServer, MCPSSEServer, MCPSHTTPServer } from "#/types/settings";
import { BrandButton } from "../brand-button";
import { SettingsInput } from "../settings-input";
import { OptionalTag } from "../optional-tag";

interface MCPServerFormProps {
  mode: "add" | "edit";
  server: MCPServerConfig | null;
  onSave: (server: Omit<MCPServerConfig, "id">) => void;
  onCancel: () => void;
}

export function MCPServerForm({
  mode,
  server,
  onSave,
  onCancel,
}: MCPServerFormProps) {
  const { t } = useTranslation();

  const [serverType, setServerType] = useState<MCPServerType>("sse");
  const [formData, setFormData] = useState({
    // Common fields
    url: "",
    api_key: "",
    // Stdio specific fields
    name: "",
    command: "",
    args: "",
    env: "",
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (mode === "edit" && server) {
      setServerType(server.type);

      if (server.type === "stdio") {
        const stdioServer = server as MCPStdioServer;
        setFormData({
          url: "",
          api_key: "",
          name: stdioServer.name,
          command: stdioServer.command,
          args: stdioServer.args?.join(" ") || "",
          env: stdioServer.env
            ? Object.entries(stdioServer.env)
                .map(([k, v]) => `${k}=${v}`)
                .join(", ")
            : "",
        });
      } else {
        const urlServer = server as MCPSSEServer | MCPSHTTPServer;
        setFormData({
          url: urlServer.url,
          api_key: urlServer.api_key || "",
          name: "",
          command: "",
          args: "",
          env: "",
        });
      }
    } else {
      // Reset form for add mode
      setFormData({
        url: "",
        api_key: "",
        name: "",
        command: "",
        args: "",
        env: "",
      });
    }
  }, [mode, server]);

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (serverType === "stdio") {
      if (!formData.name.trim()) {
        newErrors.name = t(I18nKey.SETTINGS$MCP_ERROR_NAME_REQUIRED);
      } else if (!/^[a-zA-Z0-9_-]+$/.test(formData.name.trim())) {
        newErrors.name = t(I18nKey.SETTINGS$MCP_ERROR_NAME_INVALID);
      }

      if (!formData.command.trim()) {
        newErrors.command = t(I18nKey.SETTINGS$MCP_ERROR_COMMAND_REQUIRED);
      } else if (formData.command.trim().includes(" ")) {
        newErrors.command = t(I18nKey.SETTINGS$MCP_ERROR_COMMAND_NO_SPACES);
      }

      // Validate environment variables format
      if (formData.env.trim()) {
        const envPairs = formData.env
          .split(",")
          .map((pair) => pair.trim())
          .filter(Boolean);
        for (const pair of envPairs) {
          if (!pair.includes("=")) {
            newErrors.env = t(I18nKey.SETTINGS$MCP_ERROR_ENV_FORMAT);
            break;
          }
          const [key] = pair.split("=", 1);
          if (!key.trim() || !/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(key.trim())) {
            newErrors.env = t(I18nKey.SETTINGS$MCP_ERROR_ENV_KEY_INVALID);
            break;
          }
        }
      }
    } else if (!formData.url.trim()) {
      newErrors.url = t(I18nKey.SETTINGS$MCP_ERROR_URL_REQUIRED);
    } else {
      try {
        const url = new URL(formData.url.trim());
        if (!["http:", "https:", "ws:", "wss:"].includes(url.protocol)) {
          newErrors.url = t(I18nKey.SETTINGS$MCP_ERROR_URL_PROTOCOL);
        }
      } catch {
        newErrors.url = t(I18nKey.SETTINGS$MCP_ERROR_URL_INVALID);
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    if (serverType === "stdio") {
      const stdioServer: Omit<MCPServerConfig, "id"> = {
        type: "stdio",
        name: formData.name.trim(),
        command: formData.command.trim(),
        args: formData.args.trim()
          ? formData.args.trim().split(/\s+/)
          : undefined,
        env: formData.env.trim()
          ? Object.fromEntries(
              formData.env
                .split(",")
                .map((pair) => pair.trim())
                .filter(Boolean)
                .map((pair) => {
                  const [key, ...valueParts] = pair.split("=");
                  return [key.trim(), valueParts.join("=")];
                }),
            )
          : undefined,
      };
      onSave(stdioServer);
    } else {
      const urlServer: Omit<MCPServerConfig, "id"> = {
        type: serverType,
        url: formData.url.trim(),
        api_key: formData.api_key.trim() || undefined,
      };
      onSave(urlServer);
    }
  };

  const handleInputChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: "" }));
    }
  };

  return (
    <div className="border border-tertiary rounded-md p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-medium">
          {mode === "add"
            ? t(I18nKey.SETTINGS$MCP_ADD_SERVER)
            : t(I18nKey.SETTINGS$MCP_EDIT_SERVER)}
        </h3>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {mode === "add" && (
          <div>
            <label className="block text-sm font-medium mb-2">
              {t(I18nKey.SETTINGS$MCP_SERVER_TYPE)}
            </label>
            <select
              value={serverType}
              onChange={(e) => setServerType(e.target.value as MCPServerType)}
              className="w-full px-3 py-2 border border-tertiary rounded-md bg-base-secondary text-content-1 focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="sse">
                {t(I18nKey.SETTINGS$MCP_SERVER_TYPE_SSE)}
              </option>
              <option value="stdio">
                {t(I18nKey.SETTINGS$MCP_SERVER_TYPE_STDIO)}
              </option>
              <option value="shttp">
                {t(I18nKey.SETTINGS$MCP_SERVER_TYPE_SHTTP)}
              </option>
            </select>
          </div>
        )}

        {serverType === "stdio" ? (
          <>
            <SettingsInput
              label={t(I18nKey.SETTINGS$MCP_NAME)}
              value={formData.name}
              onChange={(value) => handleInputChange("name", value)}
              placeholder={t(I18nKey.SETTINGS$MCP_NAME_PLACEHOLDER)}
              error={errors.name}
              required
            />

            <SettingsInput
              label={t(I18nKey.SETTINGS$MCP_COMMAND)}
              value={formData.command}
              onChange={(value) => handleInputChange("command", value)}
              placeholder={t(I18nKey.SETTINGS$MCP_COMMAND_PLACEHOLDER)}
              error={errors.command}
              required
            />

            <div>
              <div className="flex items-center gap-2 mb-2">
                <label className="text-sm font-medium">
                  {t(I18nKey.SETTINGS$MCP_ARGS)}
                </label>
                <OptionalTag />
              </div>
              <SettingsInput
                value={formData.args}
                onChange={(value) => handleInputChange("args", value)}
                placeholder={t(I18nKey.SETTINGS$MCP_ARGS_PLACEHOLDER)}
                error={errors.args}
              />
              <p className="text-xs text-content-3 mt-1">
                {t(I18nKey.SETTINGS$MCP_ARGS_HELP)}
              </p>
            </div>

            <div>
              <div className="flex items-center gap-2 mb-2">
                <label className="text-sm font-medium">
                  {t(I18nKey.SETTINGS$MCP_ENV)}
                </label>
                <OptionalTag />
              </div>
              <SettingsInput
                value={formData.env}
                onChange={(value) => handleInputChange("env", value)}
                placeholder={t(I18nKey.SETTINGS$MCP_ENV_PLACEHOLDER)}
                error={errors.env}
              />
              <p className="text-xs text-content-3 mt-1">
                {t(I18nKey.SETTINGS$MCP_ENV_HELP)}
              </p>
            </div>
          </>
        ) : (
          <>
            <SettingsInput
              label={t(I18nKey.SETTINGS$MCP_URL)}
              value={formData.url}
              onChange={(value) => handleInputChange("url", value)}
              placeholder={t(I18nKey.SETTINGS$MCP_URL_PLACEHOLDER)}
              error={errors.url}
              required
            />

            <div>
              <div className="flex items-center gap-2 mb-2">
                <label className="text-sm font-medium">
                  {t(I18nKey.SETTINGS$MCP_API_KEY)}
                </label>
                <OptionalTag />
              </div>
              <SettingsInput
                value={formData.api_key}
                onChange={(value) => handleInputChange("api_key", value)}
                placeholder={t(I18nKey.SETTINGS$MCP_API_KEY_PLACEHOLDER)}
                type="password"
              />
              <p className="text-xs text-content-3 mt-1">
                {t(I18nKey.SETTINGS$MCP_API_KEY_HELP)}
              </p>
            </div>
          </>
        )}

        <div className="flex gap-4 pt-4 border-t border-tertiary">
          <BrandButton
            type="submit"
            variant="primary"
            testId="save-mcp-server-button"
          >
            {mode === "add"
              ? t(I18nKey.SETTINGS$MCP_ADD_SERVER)
              : t(I18nKey.SETTINGS$SAVE_CHANGES)}
          </BrandButton>

          <BrandButton
            type="button"
            variant="secondary"
            onClick={onCancel}
            testId="cancel-mcp-server-button"
          >
            {t(I18nKey.SETTINGS$CANCEL)}
          </BrandButton>
        </div>
      </form>
    </div>
  );
}
