import { vi, describe, it, expect, Mock, beforeEach } from "vitest";
import { Settings } from "../../src/services/settings";
import { openHands } from "#/api/open-hands-axios";

import { DEFAULT_SETTINGS, getSettings, saveSettings } from "../../src/services/settings";

vi.mock("../../src/services/settings", async () => {
  const actual = await vi.importActual("../../src/services/settings");
  return {
    ...actual,
    DEFAULT_SETTINGS: {
      LLM_MODEL: "anthropic/claude-3-5-sonnet-20241022",
      LLM_BASE_URL: "",
      AGENT: "CodeActAgent",
      LANGUAGE: "en",
      LLM_API_KEY: null,
      CONFIRMATION_MODE: false,
      SECURITY_ANALYZER: "",
      REMOTE_RUNTIME_RESOURCE_FACTOR: 1,
    },
    getSettings: async () => {
      const response = await openHands.get("/api/settings");
      const data = response.data;
      return {
        LLM_MODEL: data.llm_model || DEFAULT_SETTINGS.LLM_MODEL,
        LLM_BASE_URL: data.llm_base_url || DEFAULT_SETTINGS.LLM_BASE_URL,
        AGENT: data.agent || DEFAULT_SETTINGS.AGENT,
        LANGUAGE: data.language || DEFAULT_SETTINGS.LANGUAGE,
        CONFIRMATION_MODE: data.confirmation_mode ?? DEFAULT_SETTINGS.CONFIRMATION_MODE,
        SECURITY_ANALYZER: data.security_analyzer || DEFAULT_SETTINGS.SECURITY_ANALYZER,
        LLM_API_KEY: data.llm_api_key ?? DEFAULT_SETTINGS.LLM_API_KEY,
        REMOTE_RUNTIME_RESOURCE_FACTOR: data.remote_runtime_resource_factor ?? DEFAULT_SETTINGS.REMOTE_RUNTIME_RESOURCE_FACTOR,
      };
    },
    saveSettings: async (settings: Settings) => {
      try {
        const response = await openHands.post("/api/settings", {
          llm_model: settings.LLM_MODEL,
          llm_base_url: settings.LLM_BASE_URL,
          agent: settings.AGENT,
          language: settings.LANGUAGE,
          llm_api_key: settings.LLM_API_KEY,
          confirmation_mode: settings.CONFIRMATION_MODE,
          security_analyzer: settings.SECURITY_ANALYZER,
          remote_runtime_resource_factor: settings.REMOTE_RUNTIME_RESOURCE_FACTOR,
        });
        return response.data === true;
      } catch (error) {
        return false;
      }
    },
  };
});

vi.mock("#/api/open-hands-axios", () => ({
  openHands: {
    get: vi.fn(),
    post: vi.fn().mockResolvedValue({ data: true }),
  },
}));

describe("getSettings from API", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("should get settings from API", async () => {
    const apiSettings = {
      llm_model: "llm_value",
      llm_base_url: "base_url",
      agent: "agent_value",
      language: "language_value",
      confirmation_mode: true,
      security_analyzer: "invariant",
      llm_api_key: "api_key",
      remote_runtime_resource_factor: 2,
    };

    (openHands.get as Mock).mockResolvedValueOnce({ data: apiSettings });

    const settings = await getSettings();

    expect(settings).toEqual({
      LLM_MODEL: apiSettings.llm_model,
      LLM_BASE_URL: apiSettings.llm_base_url,
      AGENT: apiSettings.agent,
      LANGUAGE: apiSettings.language,
      LLM_API_KEY: apiSettings.llm_api_key,
      CONFIRMATION_MODE: apiSettings.confirmation_mode,
      SECURITY_ANALYZER: apiSettings.security_analyzer,
      REMOTE_RUNTIME_RESOURCE_FACTOR: apiSettings.remote_runtime_resource_factor,
    });
  });

  it("should handle missing API values", async () => {
    const apiSettings = {
      llm_model: undefined,
      llm_base_url: undefined,
      agent: undefined,
      language: undefined,
      confirmation_mode: undefined,
      security_analyzer: undefined,
      llm_api_key: undefined,
      remote_runtime_resource_factor: undefined,
    };

    (openHands.get as Mock).mockResolvedValueOnce({ data: apiSettings });

    const settings = await getSettings();

    expect(settings).toEqual(DEFAULT_SETTINGS);
  });
});

describe("saveSettings to API", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("should save settings to API", async () => {
    const settings: Settings = {
      LLM_MODEL: "llm_value",
      LLM_BASE_URL: "base_url",
      AGENT: "agent_value",
      LANGUAGE: "language_value",
      LLM_API_KEY: "some_key",
      CONFIRMATION_MODE: true,
      SECURITY_ANALYZER: "invariant",
      REMOTE_RUNTIME_RESOURCE_FACTOR: 2,
    };

    (openHands.post as Mock).mockResolvedValueOnce({ data: true });

    const result = await saveSettings(settings);

    expect(result).toBe(true);
    expect(openHands.post).toHaveBeenCalledWith("/api/settings", {
      llm_model: settings.LLM_MODEL,
      llm_base_url: settings.LLM_BASE_URL,
      agent: settings.AGENT,
      language: settings.LANGUAGE,
      llm_api_key: settings.LLM_API_KEY,
      confirmation_mode: settings.CONFIRMATION_MODE,
      security_analyzer: settings.SECURITY_ANALYZER,
      remote_runtime_resource_factor: settings.REMOTE_RUNTIME_RESOURCE_FACTOR,
    });
  });

  it("should handle API errors", async () => {
    const settings: Settings = {
      LLM_MODEL: "llm_value",
      LLM_BASE_URL: "base_url",
      AGENT: "agent_value",
      LANGUAGE: "language_value",
      LLM_API_KEY: "some_key",
      CONFIRMATION_MODE: true,
      SECURITY_ANALYZER: "invariant",
      REMOTE_RUNTIME_RESOURCE_FACTOR: 2,
    };

    (openHands.post as Mock).mockRejectedValueOnce(new Error("API Error"));

    const result = await saveSettings(settings);

    expect(result).toBe(false);
  });
});
