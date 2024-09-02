import { describe, expect, it, vi, Mock } from "vitest";
import {
  DEFAULT_SETTINGS,
  Settings,
  getSettings,
  getSettingsDifference,
  saveSettings,
} from "./settings";

Storage.prototype.getItem = vi.fn();
Storage.prototype.setItem = vi.fn();

afterEach(() => {
  vi.resetAllMocks();
});

describe("getSettings", () => {
  it("should get the stored settings", () => {
    (localStorage.getItem as Mock)
      .mockReturnValueOnce("llm_value")
      .mockReturnValueOnce("custom_llm_value")
      .mockReturnValueOnce("true")
      .mockReturnValueOnce("agent_value")
      .mockReturnValueOnce("language_value")
      .mockReturnValueOnce("api_key")
      .mockReturnValueOnce("true")
      .mockReturnValueOnce("invariant");

    const settings = getSettings();

    expect(settings).toEqual({
      LLM_MODEL: "llm_value",
      CUSTOM_LLM_MODEL: "custom_llm_value",
      USING_CUSTOM_MODEL: true,
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
      CUSTOM_LLM_MODEL: "",
      USING_CUSTOM_MODEL: DEFAULT_SETTINGS.USING_CUSTOM_MODEL,
      AGENT: DEFAULT_SETTINGS.AGENT,
      LANGUAGE: DEFAULT_SETTINGS.LANGUAGE,
      LLM_API_KEY: "",
      CONFIRMATION_MODE: DEFAULT_SETTINGS.CONFIRMATION_MODE,
      SECURITY_ANALYZER: DEFAULT_SETTINGS.SECURITY_ANALYZER,
    });
  });
});

describe("saveSettings", () => {
  it("should save the settings", () => {
    const settings: Settings = {
      LLM_MODEL: "llm_value",
      CUSTOM_LLM_MODEL: "custom_llm_value",
      USING_CUSTOM_MODEL: true,
      AGENT: "agent_value",
      LANGUAGE: "language_value",
      LLM_API_KEY: "some_key",
      CONFIRMATION_MODE: true,
      SECURITY_ANALYZER: "invariant",
    };

    saveSettings(settings);

    expect(localStorage.setItem).toHaveBeenCalledWith("LLM_MODEL", "llm_value");
    expect(localStorage.setItem).toHaveBeenCalledWith(
      "CUSTOM_LLM_MODEL",
      "custom_llm_value",
    );
    expect(localStorage.setItem).toHaveBeenCalledWith(
      "USING_CUSTOM_MODEL",
      "true",
    );
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

  it("should save partial settings", () => {
    const settings = {
      LLM_MODEL: "llm_value",
    };

    saveSettings(settings);

    expect(localStorage.setItem).toHaveBeenCalledTimes(2);
    expect(localStorage.setItem).toHaveBeenCalledWith("LLM_MODEL", "llm_value");
    expect(localStorage.setItem).toHaveBeenCalledWith("SETTINGS_VERSION", "1");
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

describe("getSettingsDifference", () => {
  beforeEach(() => {
    (localStorage.getItem as Mock)
      .mockReturnValueOnce("llm_value")
      .mockReturnValueOnce("custom_llm_value")
      .mockReturnValueOnce("false")
      .mockReturnValueOnce("agent_value")
      .mockReturnValueOnce("language_value");
  });

  it("should return updated settings", () => {
    const settings = {
      LLM_MODEL: "new_llm_value",
      CUSTOM_LLM_MODEL: "custom_llm_value",
      USING_CUSTOM_MODEL: true,
      AGENT: "new_agent_value",
      LANGUAGE: "language_value",
    };

    const updatedSettings = getSettingsDifference(settings);

    expect(updatedSettings).toEqual({
      USING_CUSTOM_MODEL: true,
      LLM_MODEL: "new_llm_value",
      AGENT: "new_agent_value",
    });
  });

  it("should not handle invalid settings", () => {
    const settings = {
      LLM_MODEL: "new_llm_value",
      AGENT: "new_agent_value",
      INVALID: "invalid_value",
    };

    const updatedSettings = getSettingsDifference(settings);

    expect(updatedSettings).toEqual({
      LLM_MODEL: "new_llm_value",
      AGENT: "new_agent_value",
    });
  });
});
