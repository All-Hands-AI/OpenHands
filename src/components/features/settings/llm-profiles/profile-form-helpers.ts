import {
  LLM_AUTH_TYPE_API_KEY,
  LLM_AUTH_TYPE_KEY,
  LLM_AUTH_TYPE_SUBSCRIPTION,
  LLM_SUBSCRIPTION_VENDOR_KEY,
  OPENAI_SUBSCRIPTION_VENDOR,
  resolveLlmAuthType,
} from "#/constants/llm-subscription";
import type { SettingsSchema } from "#/types/settings";
import { isOpenHandsProviderModel } from "#/utils/format-model-name";
import {
  normalizeFieldValue,
  type SettingsFormValues,
  type SettingsView,
} from "#/utils/sdk-settings-schema";

/** Form-values key for the shared provider connection a profile links to. */
export const LLM_PROVIDER_CONNECTION_KEY = "llm.provider_connection_id";

export interface BuildProfileLlmConfigOptions {
  baseConfig?: Record<string, unknown> | null;
  dirtyLlm: Record<string, unknown>;
  formValues: SettingsFormValues;
  view?: SettingsView;
  supportsConnections?: boolean;
  isCloud?: boolean;
}

/**
 * Maps a profile's flat LLM config into schema-aware form values (with `llm.` prefixes).
 * Ensures all schema-defined fields are normalized, with fallback defaults for key settings.
 */
export function profileToFormValues(
  config: Record<string, unknown>,
  schema?: SettingsSchema | null,
): SettingsFormValues {
  const llmFields =
    schema?.sections.find((section) => section.key === "llm")?.fields ?? [];
  const formValues: SettingsFormValues = {};

  for (const field of llmFields) {
    const flatKey = field.key.startsWith("llm.")
      ? field.key.slice("llm.".length)
      : field.key;
    formValues[field.key] = normalizeFieldValue(field, config[flatKey]);
  }

  // Safety net for specially-rendered keys when the schema is unavailable.
  if (llmFields.length === 0) {
    formValues["llm.model"] = (config.model as string) ?? "";
    formValues["llm.api_key"] = (config.api_key as string) ?? "";
    formValues["llm.base_url"] = (config.base_url as string) ?? "";
    formValues[LLM_AUTH_TYPE_KEY] = resolveLlmAuthType(config.auth_type);
    formValues[LLM_SUBSCRIPTION_VENDOR_KEY] =
      (config.subscription_vendor as string) ?? OPENAI_SUBSCRIPTION_VENDOR;
  }

  // Seed the provider-connection link explicitly so an unchanged profile keeps its link.
  formValues[LLM_PROVIDER_CONNECTION_KEY] =
    typeof config.provider_connection_id === "string"
      ? config.provider_connection_id
      : "";

  return formValues;
}

/**
 * Creates form values for a fresh profile using schema defaults and the given default model.
 * Overrides all schema llm.* fields so no stale settings from `agent_settings.llm` leak in.
 */
export function freshProfileFormValues(
  defaultModel: string,
  schema?: SettingsSchema | null,
): SettingsFormValues {
  const llmFields =
    schema?.sections.find((section) => section.key === "llm")?.fields ?? [];
  const formValues: SettingsFormValues = {};

  for (const field of llmFields) {
    formValues[field.key] = normalizeFieldValue(field, field.default);
  }

  formValues["llm.model"] = defaultModel;
  formValues["llm.api_key"] = "";
  formValues["llm.base_url"] = "";
  formValues[LLM_PROVIDER_CONNECTION_KEY] = "";
  formValues[LLM_AUTH_TYPE_KEY] = LLM_AUTH_TYPE_API_KEY;
  formValues[LLM_SUBSCRIPTION_VENDOR_KEY] = OPENAI_SUBSCRIPTION_VENDOR;

  return formValues;
}

/**
 * Builds a clean LLM config payload for saving as a profile by merging user edits over baseConfig.
 * Follows the profile editor rules:
 * - Drops hidden base_url if model was changed in Basic view.
 * - Retains baseConfig.api_key if the user did not type a new key.
 * - Strips api_key and base_url for subscription auth or provider connections.
 */
export function buildProfileLlmConfig({
  baseConfig = {},
  dirtyLlm,
  formValues,
  view = "basic",
  supportsConnections = false,
  isCloud = false,
}: BuildProfileLlmConfigOptions): Record<string, unknown> {
  const base = baseConfig ? { ...baseConfig } : {};
  const didChangeModelInBasic =
    view === "basic" &&
    Object.prototype.hasOwnProperty.call(dirtyLlm, "model") &&
    dirtyLlm.model !== base.model;
  const llmConfig: Record<string, unknown> = { ...base, ...dirtyLlm };
  const authType = resolveLlmAuthType(llmConfig.auth_type);

  const connectionId = supportsConnections
    ? String(formValues[LLM_PROVIDER_CONNECTION_KEY] ?? "").trim()
    : "";

  if (authType === LLM_AUTH_TYPE_SUBSCRIPTION) {
    llmConfig.auth_type = LLM_AUTH_TYPE_SUBSCRIPTION;
    llmConfig.subscription_vendor = OPENAI_SUBSCRIPTION_VENDOR;
    llmConfig.provider_connection_id = null;
    delete llmConfig.api_key;
    delete llmConfig.base_url;
  } else if (connectionId) {
    llmConfig.auth_type = LLM_AUTH_TYPE_API_KEY;
    llmConfig.subscription_vendor = null;
    llmConfig.provider_connection_id = connectionId;
    delete llmConfig.api_key;
    delete llmConfig.base_url;
  } else {
    llmConfig.auth_type = LLM_AUTH_TYPE_API_KEY;
    llmConfig.subscription_vendor = null;
    if (supportsConnections) llmConfig.provider_connection_id = null;

    const isCloudOpenHandsProvider =
      isCloud &&
      isOpenHandsProviderModel(
        typeof llmConfig.model === "string" ? llmConfig.model : "",
      );
    if (isCloudOpenHandsProvider) {
      delete llmConfig.api_key;
      delete llmConfig.base_url;
    } else {
      if (didChangeModelInBasic) {
        delete llmConfig.base_url;
      }

      if (
        typeof llmConfig.api_key !== "string" ||
        llmConfig.api_key.trim() === ""
      ) {
        const existingKey =
          typeof base.api_key === "string" ? base.api_key : "";
        if (existingKey) {
          llmConfig.api_key = existingKey;
        } else {
          delete llmConfig.api_key;
        }
      }
    }
  }

  return llmConfig;
}
