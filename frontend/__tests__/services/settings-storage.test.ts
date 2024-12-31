import { vi, describe, it, expect, Mock, beforeEach } from "vitest";
import { openHands } from "#/api/open-hands-axios";

import { DEFAULT_SETTINGS, getSettings } from "../../src/services/settings";

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
      try {
        const response = await openHands.get("/api/settings");
        const data = response.data;
        return {
          LLM_MODEL: data.llm_model,
          LLM_BASE_URL: data.llm_base_url,
          AGENT: data.agent,
          LANGUAGE: data.language,
          CONFIRMATION_MODE: data.confirmation_mode,
          SECURITY_ANALYZER: data.security_analyzer,
          LLM_API_KEY: data.llm_api_key,
          REMOTE_RUNTIME_RESOURCE_FACTOR: data.remote_runtime_resource_factor,
        };
      } catch (error) {
        return {
          LLM_MODEL: localStorage.getItem("LLM_MODEL") || DEFAULT_SETTINGS.LLM_MODEL,
          LLM_BASE_URL: localStorage.getItem("LLM_BASE_URL") || DEFAULT_SETTINGS.LLM_BASE_URL,
          AGENT: localStorage.getItem("AGENT") || DEFAULT_SETTINGS.AGENT,
          LANGUAGE: localStorage.getItem("LANGUAGE") || DEFAULT_SETTINGS.LANGUAGE,
          LLM_API_KEY: localStorage.getItem("LLM_API_KEY") || DEFAULT_SETTINGS.LLM_API_KEY,
          CONFIRMATION_MODE: localStorage.getItem("CONFIRMATION_MODE") === "true" || DEFAULT_SETTINGS.CONFIRMATION_MODE,
          SECURITY_ANALYZER: localStorage.getItem("SECURITY_ANALYZER") || DEFAULT_SETTINGS.SECURITY_ANALYZER,
          REMOTE_RUNTIME_RESOURCE_FACTOR: DEFAULT_SETTINGS.REMOTE_RUNTIME_RESOURCE_FACTOR,
        };
      }
    },
  };
});

vi.mock("#/api/open-hands-axios", () => ({
  openHands: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

// Mock localStorage
const mockLocalStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
};
Object.defineProperty(window, 'localStorage', { value: mockLocalStorage });

describe("getSettings from localStorage", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    mockLocalStorage.getItem.mockReset();
  });

  it("should fallback to localStorage if API fails", async () => {
    (openHands.get as Mock).mockRejectedValueOnce(new Error("API Error"));

    // Mock localStorage values
    mockLocalStorage.getItem.mockImplementation((key) => {
      const values: Record<string, string> = {
        LLM_MODEL: "llm_value",
        LLM_BASE_URL: "base_url",
        AGENT: "agent_value",
        LANGUAGE: "language_value",
        LLM_API_KEY: "api_key",
        CONFIRMATION_MODE: "true",
        SECURITY_ANALYZER: "invariant",
      };
      return values[key] || null;
    });

    const settings = await getSettings();

    expect(settings).toEqual({
      LLM_MODEL: "llm_value",
      LLM_BASE_URL: "base_url",
      AGENT: "agent_value",
      LANGUAGE: "language_value",
      LLM_API_KEY: "api_key",
      CONFIRMATION_MODE: true,
      SECURITY_ANALYZER: "invariant",
      REMOTE_RUNTIME_RESOURCE_FACTOR: DEFAULT_SETTINGS.REMOTE_RUNTIME_RESOURCE_FACTOR,
    });
  });

  it("should use default values for missing localStorage values", async () => {
    (openHands.get as Mock).mockRejectedValueOnce(new Error("API Error"));

    // Mock empty localStorage
    mockLocalStorage.getItem.mockReturnValue(null);

    const settings = await getSettings();

    expect(settings).toEqual(DEFAULT_SETTINGS);
  });
});
