import { describe, expect, it } from "vitest";
import {
  buildProfileLlmConfig,
  freshProfileFormValues,
  profileToFormValues,
} from "#/components/features/settings/llm-profiles/profile-form-helpers";
import {
  LLM_AUTH_TYPE_API_KEY,
  LLM_AUTH_TYPE_KEY,
  LLM_AUTH_TYPE_SUBSCRIPTION,
  LLM_SUBSCRIPTION_VENDOR_KEY,
  OPENAI_SUBSCRIPTION_VENDOR,
} from "#/constants/llm-subscription";
import { LLM_PROVIDER_CONNECTION_KEY } from "#/routes/llm-settings";
import type { SettingsSchema } from "#/types/settings";

const sampleSchema: SettingsSchema = {
  model_name: "test-model",
  sections: [
    {
      key: "llm",
      label: "LLM",
      fields: [
        {
          key: "llm.model",
          label: "Model",
          value_type: "string",
          default: "openai/gpt-5",
          choices: [],
          section: "llm",
          section_label: "LLM",
          depends_on: [],
          prominence: "critical",
          secret: false,
          required: true,
        },
        {
          key: "llm.api_key",
          label: "API Key",
          value_type: "string",
          default: "",
          choices: [],
          section: "llm",
          section_label: "LLM",
          depends_on: [],
          prominence: "critical",
          secret: true,
          required: false,
        },
        {
          key: "llm.base_url",
          label: "Base URL",
          value_type: "string",
          default: "",
          choices: [],
          section: "llm",
          section_label: "LLM",
          depends_on: [],
          prominence: "major",
          secret: false,
          required: false,
        },
        {
          key: "llm.temperature",
          label: "Temperature",
          value_type: "number",
          default: 0.7,
          choices: [],
          section: "llm",
          section_label: "LLM",
          depends_on: [],
          prominence: "minor",
          secret: false,
          required: false,
        },
      ],
    },
  ],
};

describe("profile-form-helpers", () => {
  describe("profileToFormValues", () => {
    it("maps profile config to schema form fields and extracts provider connection", () => {
      const config = {
        model: "anthropic/claude-3-7-sonnet",
        api_key: "enc:secret",
        base_url: "https://custom.api.com",
        temperature: 0.2,
        provider_connection_id: "conn-123",
      };

      const values = profileToFormValues(config, sampleSchema);
      expect(values).toEqual({
        "llm.model": "anthropic/claude-3-7-sonnet",
        "llm.api_key": "enc:secret",
        "llm.base_url": "https://custom.api.com",
        "llm.temperature": "0.2",
        [LLM_PROVIDER_CONNECTION_KEY]: "conn-123",
      });
    });

    it("falls back to default keys when schema is empty or missing", () => {
      const config = {
        model: "openai/gpt-4o",
        api_key: "enc:test",
        base_url: "https://api.openai.com",
        auth_type: "api_key",
      };

      const values = profileToFormValues(config, null);
      expect(values["llm.model"]).toBe("openai/gpt-4o");
      expect(values["llm.api_key"]).toBe("enc:test");
      expect(values["llm.base_url"]).toBe("https://api.openai.com");
      expect(values[LLM_AUTH_TYPE_KEY]).toBe(LLM_AUTH_TYPE_API_KEY);
      expect(values[LLM_SUBSCRIPTION_VENDOR_KEY]).toBe(
        OPENAI_SUBSCRIPTION_VENDOR,
      );
    });
  });

  describe("freshProfileFormValues", () => {
    it("constructs form values from schema defaults and given default model", () => {
      const values = freshProfileFormValues("openai/gpt-5.6-sol", sampleSchema);
      expect(values["llm.model"]).toBe("openai/gpt-5.6-sol");
      expect(values["llm.api_key"]).toBe("");
      expect(values["llm.base_url"]).toBe("");
      expect(values["llm.temperature"]).toBe("0.7");
      expect(values[LLM_PROVIDER_CONNECTION_KEY]).toBe("");
      expect(values[LLM_AUTH_TYPE_KEY]).toBe(LLM_AUTH_TYPE_API_KEY);
      expect(values[LLM_SUBSCRIPTION_VENDOR_KEY]).toBe(
        OPENAI_SUBSCRIPTION_VENDOR,
      );
    });
  });

  describe("buildProfileLlmConfig", () => {
    it("drops base_url when model is changed in basic view", () => {
      const baseConfig = {
        model: "openai/gpt-4o",
        base_url: "https://old.custom.url",
        api_key: "enc:old-key",
      };
      const dirtyLlm = {
        model: "openai/gpt-5",
      };
      const formValues = {
        "llm.model": "openai/gpt-5",
      };

      const result = buildProfileLlmConfig({
        baseConfig,
        dirtyLlm,
        formValues,
        view: "basic",
      });

      expect(result.model).toBe("openai/gpt-5");
      expect(result.base_url).toBeUndefined();
      expect(result.api_key).toBe("enc:old-key");
    });

    it("preserves base_url when model is changed in advanced/all view", () => {
      const baseConfig = {
        model: "openai/gpt-4o",
        base_url: "https://custom.endpoint.com/v1",
        api_key: "enc:old-key",
      };
      const dirtyLlm = {
        model: "openai/deepseek-v4-flash",
      };
      const formValues = {
        "llm.model": "openai/deepseek-v4-flash",
        "llm.base_url": "https://custom.endpoint.com/v1",
      };

      const result = buildProfileLlmConfig({
        baseConfig,
        dirtyLlm,
        formValues,
        view: "all",
      });

      expect(result.model).toBe("openai/deepseek-v4-flash");
      expect(result.base_url).toBe("https://custom.endpoint.com/v1");
      expect(result.api_key).toBe("enc:old-key");
    });

    it("strips api_key and base_url for subscription auth", () => {
      const baseConfig = {
        model: "openai/gpt-5.6-luna",
        api_key: "some-key",
      };
      const dirtyLlm = {
        auth_type: LLM_AUTH_TYPE_SUBSCRIPTION,
      };
      const formValues = {
        [LLM_AUTH_TYPE_KEY]: LLM_AUTH_TYPE_SUBSCRIPTION,
      };

      const result = buildProfileLlmConfig({
        baseConfig,
        dirtyLlm,
        formValues,
        view: "basic",
      });

      expect(result.auth_type).toBe(LLM_AUTH_TYPE_SUBSCRIPTION);
      expect(result.subscription_vendor).toBe(OPENAI_SUBSCRIPTION_VENDOR);
      expect(result.api_key).toBeUndefined();
      expect(result.base_url).toBeUndefined();
    });

    it("attaches provider_connection_id and strips inline credentials when linked", () => {
      const baseConfig = {
        model: "openai/gpt-5",
        api_key: "old-key",
      };
      const dirtyLlm = {};
      const formValues = {
        [LLM_PROVIDER_CONNECTION_KEY]: "conn-999",
      };

      const result = buildProfileLlmConfig({
        baseConfig,
        dirtyLlm,
        formValues,
        supportsConnections: true,
      });

      expect(result.provider_connection_id).toBe("conn-999");
      expect(result.api_key).toBeUndefined();
      expect(result.base_url).toBeUndefined();
    });
  });
});
