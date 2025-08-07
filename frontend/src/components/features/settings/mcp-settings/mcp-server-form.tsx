import React from "react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { SettingsInput } from "../settings-input";
import { SettingsDropdownInput } from "../settings-dropdown-input";
import { BrandButton } from "../brand-button";
import { OptionalTag } from "../optional-tag";
import { cn } from "#/utils/utils";

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

interface MCPServerFormProps {
  mode: "add" | "edit";
  server?: MCPServerConfig;
  onSubmit: (server: MCPServerConfig) => void;
  onCancel: () => void;
}

export function MCPServerForm({ mode, server, onSubmit, onCancel }: MCPServerFormProps) {
  const { t } = useTranslation();
  const [serverType, setServerType] = React.useState<MCPServerType>(
    server?.type || "sse"
  );
  const [error, setError] = React.useState<string | null>(null);

  const serverTypeOptions = [
    { key: "sse", label: t(I18nKey.SETTINGS$MCP_SERVER_TYPE_SSE) },
    { key: "stdio", label: t(I18nKey.SETTINGS$MCP_SERVER_TYPE_STDIO) },
    { key: "shttp", label: t(I18nKey.SETTINGS$MCP_SERVER_TYPE_SHTTP) },
  ];

  const validateForm = (formData: FormData): string | null => {
    if (serverType === "sse" || serverType === "shttp") {
      const url = formData.get("url")?.toString().trim();
      if (!url) {
        return t(I18nKey.SETTINGS$MCP_ERROR_URL_REQUIRED);
      }
      try {
        const urlObj = new URL(url);
        if (!["http:", "https:"].includes(urlObj.protocol)) {
          return t(I18nKey.SETTINGS$MCP_ERROR_URL_INVALID_PROTOCOL);
        }
      } catch {
        return t(I18nKey.SETTINGS$MCP_ERROR_URL_INVALID);
      }
    }

    if (serverType === "stdio") {
      const name = formData.get("name")?.toString().trim();
      const command = formData.get("command")?.toString().trim();

      if (!name) {
        return t(I18nKey.SETTINGS$MCP_ERROR_NAME_REQUIRED);
      }
      if (!/^[a-zA-Z0-9_-]+$/.test(name)) {
        return t(I18nKey.SETTINGS$MCP_ERROR_NAME_INVALID);
      }
      if (!command) {
        return t(I18nKey.SETTINGS$MCP_ERROR_COMMAND_REQUIRED);
      }
      if (command.includes(" ")) {
        return t(I18nKey.SETTINGS$MCP_ERROR_COMMAND_NO_SPACES);
      }
    }

    return null;
  };

  const parseEnvironmentVariables = (envString: string): Record<string, string> => {
    const env: Record<string, string> = {};
    if (!envString.trim()) return env;

    const lines = envString.split("\n");
    for (const line of lines) {
      const trimmedLine = line.trim();
      if (!trimmedLine) continue;

      const equalIndex = trimmedLine.indexOf("=");
      if (equalIndex === -1) continue;

      const key = trimmedLine.substring(0, equalIndex).trim();
      const value = trimmedLine.substring(equalIndex + 1).trim();
      if (key) {
        env[key] = value;
      }
    }
    return env;
  };

  const formatEnvironmentVariables = (env?: Record<string, string>): string => {
    if (!env) return "";
    return Object.entries(env)
      .map(([key, value]) => `${key}=${value}`)
      .join("\n");
  };

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);

    const formData = new FormData(event.currentTarget);
    const validationError = validateForm(formData);

    if (validationError) {
      setError(validationError);
      return;
    }

    const baseConfig = {
      id: server?.id || `${serverType}-${Date.now()}`,
      type: serverType,
    };

    if (serverType === "sse" || serverType === "shttp") {
      const url = formData.get("url")?.toString().trim();
      const api_key = formData.get("api_key")?.toString().trim();

      onSubmit({
        ...baseConfig,
        url: url!,
        ...(api_key && { api_key }),
      });
    } else if (serverType === "stdio") {
      const name = formData.get("name")?.toString().trim();
      const command = formData.get("command")?.toString().trim();
      const argsString = formData.get("args")?.toString().trim();
      const envString = formData.get("env")?.toString().trim();

      const args = argsString
        ? argsString.split("\n").map((arg) => arg.trim()).filter(Boolean)
        : [];
      const env = parseEnvironmentVariables(envString || "");

      onSubmit({
        ...baseConfig,
        name: name!,
        command: command!,
        ...(args.length > 0 && { args }),
        ...(Object.keys(env).length > 0 && { env }),
      });
    }
  };

  const formTestId = mode === "add" ? "add-mcp-server-form" : "edit-mcp-server-form";

  return (
    <form
      data-testid={formTestId}
      onSubmit={handleSubmit}
      className="flex flex-col items-start gap-6"
    >
      {mode === "add" && (
        <SettingsDropdownInput
          testId="server-type-dropdown"
          name="server-type"
          label={t(I18nKey.SETTINGS$MCP_SERVER_TYPE)}
          items={serverTypeOptions}
          selectedKey={serverType}
          onSelectionChange={(key) => setServerType(key as MCPServerType)}
          isClearable={false}
          allowsCustomValue={false}
          required
          wrapperClassName="w-full max-w-[350px]"
        />
      )}

      {error && <p className="text-red-500 text-sm">{error}</p>}

      {(serverType === "sse" || serverType === "shttp") && (
        <>
          <SettingsInput
            testId="url-input"
            name="url"
            type="url"
            label={t(I18nKey.SETTINGS$MCP_URL)}
            className="w-full max-w-[680px]"
            required
            defaultValue={server?.url || ""}
            placeholder="https://api.example.com"
          />

          <SettingsInput
            testId="api-key-input"
            name="api_key"
            type="password"
            label={t(I18nKey.SETTINGS$MCP_API_KEY)}
            className="w-full max-w-[680px]"
            showOptionalTag
            defaultValue={server?.api_key || ""}
            placeholder={t(I18nKey.SETTINGS$MCP_API_KEY_PLACEHOLDER)}
          />
        </>
      )}

      {serverType === "stdio" && (
        <>
          <SettingsInput
            testId="name-input"
            name="name"
            type="text"
            label={t(I18nKey.SETTINGS$MCP_NAME)}
            className="w-full max-w-[350px]"
            required
            defaultValue={server?.name || ""}
            placeholder="my-mcp-server"
            pattern="^[a-zA-Z0-9_-]+$"
          />

          <SettingsInput
            testId="command-input"
            name="command"
            type="text"
            label={t(I18nKey.SETTINGS$MCP_COMMAND)}
            className="w-full max-w-[680px]"
            required
            defaultValue={server?.command || ""}
            placeholder="python"
          />

          <label className="flex flex-col gap-2.5 w-full max-w-[680px]">
            <div className="flex items-center gap-2">
              <span className="text-sm">{t(I18nKey.SETTINGS$MCP_COMMAND_ARGUMENTS)}</span>
              <OptionalTag />
            </div>
            <textarea
              data-testid="args-input"
              name="args"
              rows={3}
              defaultValue={server?.args?.join("\n") || ""}
              placeholder="arg1&#10;arg2&#10;arg3"
              className={cn(
                "bg-tertiary border border-[#717888] w-full rounded-sm p-2 placeholder:italic placeholder:text-tertiary-alt resize-none",
                "disabled:bg-[#2D2F36] disabled:border-[#2D2F36] disabled:cursor-not-allowed"
              )}
            />
          </label>

          <label className="flex flex-col gap-2.5 w-full max-w-[680px]">
            <div className="flex items-center gap-2">
              <span className="text-sm">{t(I18nKey.SETTINGS$MCP_ENVIRONMENT_VARIABLES)}</span>
              <OptionalTag />
            </div>
            <textarea
              data-testid="env-input"
              name="env"
              rows={4}
              defaultValue={formatEnvironmentVariables(server?.env)}
              placeholder="KEY1=value1&#10;KEY2=value2"
              className={cn(
                "resize-none",
                "bg-tertiary border border-[#717888] rounded-sm p-2 placeholder:italic placeholder:text-tertiary-alt",
                "disabled:bg-[#2D2F36] disabled:border-[#2D2F36] disabled:cursor-not-allowed"
              )}
            />
          </label>
        </>
      )}

      <div className="flex items-center gap-4">
        <BrandButton
          testId="cancel-button"
          type="button"
          variant="secondary"
          onClick={onCancel}
        >
          {t(I18nKey.BUTTON$CANCEL)}
        </BrandButton>
        <BrandButton testId="submit-button" type="submit" variant="primary">
          {mode === "add" && t(I18nKey.SETTINGS$MCP_ADD_SERVER)}
          {mode === "edit" && t(I18nKey.SETTINGS$MCP_SAVE_SERVER)}
        </BrandButton>
      </div>
    </form>
  );
}
