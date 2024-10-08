import { describe, expect, it, vi, Mock, afterEach } from "vitest";
import {
  DEFAULT_SETTINGS,
  Settings,
  getSettings,
  saveSettings,
} from "../../src/services/settings";

Storage.prototype.getItem = vi.fn();
Storage.prototype.setItem = vi.fn();

describe("getSettings", () => {
  afterEach(() => {
    vi.resetAllMocks();
  });

  it("should get the stored settings", () => {
    (localStorage.getItem as Mock)
      .mockReturnValueOnce("llm_value")
      .mockReturnValueOnce("base_url")
      .mockReturnValueOnce("agent_value")
      .mockReturnValueOnce("language_value")
      .mockReturnValueOnce("api_key")
      .mockReturnValueOnce("true")
      .mockReturnValueOnce("invariant");

    const settings = getSettings();

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

  it("should handle return defaults if localStorage key does not exist", () => {
    (localStorage.getItem as Mock)
      .mockReturnValueOnce(null)
      .mockReturnValueOnce(null)
      .mockReturnValueOnce(null)
      .mockReturnValueOnce(null)
      .mockReturnValueOnce(null)
      .mockReturnValueOnce(null)
      .mockReturnValueOnce(null)
      .mockReturnValueOnce(null);

    const settings = getSettings();

    expect(settings).toEqual({
      LLM_MODEL: DEFAULT_SETTINGS.LLM_MODEL,
      AGENT: DEFAULT_SETTINGS.AGENT,
      LANGUAGE: DEFAULT_SETTINGS.LANGUAGE,
      LLM_API_KEY: "",
      LLM_BASE_URL: DEFAULT_SETTINGS.LLM_BASE_URL,
      CONFIRMATION_MODE: DEFAULT_SETTINGS.CONFIRMATION_MODE,
      SECURITY_ANALYZER: DEFAULT_SETTINGS.SECURITY_ANALYZER,
    });
  });
});

describe("saveSettings", () => {
  it("should save the settings", () => {
    const settings: Settings = {
      LLM_MODEL: "llm_value",
      LLM_BASE_URL: "base_url",
      AGENT: "agent_value",
      LANGUAGE: "language_value",
      LLM_API_KEY: "some_key",
      CONFIRMATION_MODE: true,
      SECURITY_ANALYZER: "invariant",
    };

    saveSettings(settings);

    expect(localStorage.setItem).toHaveBeenCalledWith("LLM_MODEL", "llm_value");
    expect(localStorage.setItem).toHaveBeenCalledWith("AGENT", "agent_value");
    expect(localStorage.setItem).toHaveBeenCalledWith(
      "LANGUAGE",
      "language_value",
    );
    expect(localStorage.setItem).toHaveBeenCalledWith(
      "LLM_API_KEY",
      "some_key",
    );
  });

  it.skip("should save partial settings", () => {
    const settings = {
      LLM_MODEL: "llm_value",
    };

    saveSettings(settings);

    expect(localStorage.setItem).toHaveBeenCalledTimes(2);
    expect(localStorage.setItem).toHaveBeenCalledWith("LLM_MODEL", "llm_value");
    expect(localStorage.setItem).toHaveBeenCalledWith("SETTINGS_VERSION", "2");
  });

  it("should not save invalid settings", () => {
    const settings = {
      LLM_MODEL: "llm_value",
      AGENT: "agent_value",
      LANGUAGE: "language_value",
      INVALID: "invalid_value",
    };

    saveSettings(settings);

    expect(localStorage.setItem).toHaveBeenCalledWith("LLM_MODEL", "llm_value");
    expect(localStorage.setItem).toHaveBeenCalledWith("AGENT", "agent_value");
    expect(localStorage.setItem).toHaveBeenCalledWith(
      "LANGUAGE",
      "language_value",
    );
    expect(localStorage.setItem).not.toHaveBeenCalledWith(
      "INVALID",
      "invalid_value",
    );
  });
});
