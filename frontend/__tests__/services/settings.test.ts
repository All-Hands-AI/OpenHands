import { describe, expect, it, vi, Mock, afterEach } from "vitest";
import {
  DEFAULT_SETTINGS,
  Settings,
  getSettings,
  saveSettings,
  getLocalStorageSettings,
} from "../../src/services/settings";
import { openHands } from "#/api/open-hands-axios";

vi.mock("#/api/open-hands-axios", () => ({
  openHands: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

Storage.prototype.getItem = vi.fn();
Storage.prototype.setItem = vi.fn();

describe("getSettings", () => {
  afterEach(() => {
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
    };

    (openHands.get as Mock).mockResolvedValueOnce({ data: apiSettings });

    const settings = await getSettings();

    expect(settings).toEqual({
      LLM_MODEL: "llm_value",
      LLM_BASE_URL: "base_url",
      AGENT: "agent_value",
      LANGUAGE: "language_value",
      LLM_API_KEY: "",
      CONFIRMATION_MODE: true,
      SECURITY_ANALYZER: "invariant",
      REMOTE_RUNTIME_RESOURCE_FACTOR: DEFAULT_SETTINGS.REMOTE_RUNTIME_RESOURCE_FACTOR,
    });
  });

  it("should fallback to localStorage if API fails", async () => {
    (openHands.get as Mock).mockResolvedValueOnce({ data: null });
    (localStorage.getItem as Mock)
      .mockReturnValueOnce("llm_value")
      .mockReturnValueOnce("base_url")
      .mockReturnValueOnce("agent_value")
      .mockReturnValueOnce("language_value")
      .mockReturnValueOnce("api_key")
      .mockReturnValueOnce("true")
      .mockReturnValueOnce("invariant");

    const settings = await getSettings();

    expect(settings).toEqual({
      LLM_MODEL: "llm_value",
      LLM_BASE_URL: "base_url",
      AGENT: "agent_value",
      LANGUAGE: "language_value",
      LLM_API_KEY: "api_key",
      CONFIRMATION_MODE: true,
      SECURITY_ANALYZER: "invariant",
    });
  });
});

describe("saveSettings", () => {
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
      llm_model: "llm_value",
      llm_base_url: "base_url",
      agent: "agent_value",
      language: "language_value",
      llm_api_key: "some_key",
      confirmation_mode: true,
      security_analyzer: "invariant",
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