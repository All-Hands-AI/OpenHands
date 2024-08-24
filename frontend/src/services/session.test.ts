import { describe, expect, it, vi } from "vitest";
import ActionType from "#/types/ActionType";
import { Settings, saveSettings } from "./settings";
import Session from "./session";

const sendSpy = vi.spyOn(Session, "send");
// @ts-expect-error - spying on private function
const setupSpy = vi.spyOn(Session, "_setupSocket").mockImplementation(() => {
  // @ts-expect-error - calling a private function
  Session._initializeAgent();
});

describe("startNewSession", () => {
  afterEach(() => {
    sendSpy.mockClear();
    setupSpy.mockClear();
  });

  it("Should start a new session with the current settings", () => {
    const settings: Settings = {
      LLM_MODEL: "llm_value",
      CUSTOM_LLM_MODEL: "",
      USING_CUSTOM_MODEL: false,
      AGENT: "agent_value",
      LANGUAGE: "language_value",
      LLM_API_KEY: "sk-...",
      CONFIRMATION_MODE: true,
      SECURITY_ANALYZER: "analyzer",
    };

    const event = {
      action: ActionType.INIT,
      args: settings,
    };

    saveSettings(settings);
    Session.startNewSession();

    expect(setupSpy).toHaveBeenCalledTimes(1);
    expect(sendSpy).toHaveBeenCalledWith(JSON.stringify(event));
  });

  it("should start with the custom llm if set", () => {
    const settings: Settings = {
      LLM_MODEL: "llm_value",
      CUSTOM_LLM_MODEL: "custom_llm_value",
      USING_CUSTOM_MODEL: true,
      AGENT: "agent_value",
      LANGUAGE: "language_value",
      LLM_API_KEY: "sk-...",
      CONFIRMATION_MODE: true,
      SECURITY_ANALYZER: "analyzer",
    };

    const event = {
      action: ActionType.INIT,
      args: settings,
    };

    saveSettings(settings);
    Session.startNewSession();

    expect(setupSpy).toHaveBeenCalledTimes(1);
    expect(sendSpy).toHaveBeenCalledWith(
      JSON.stringify({
        ...event,
        args: { ...settings, LLM_MODEL: "custom_llm_value" },
      }),
    );
  });
});
