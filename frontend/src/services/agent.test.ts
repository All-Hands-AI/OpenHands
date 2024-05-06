import { describe, expect, it, vi } from "vitest";

import ActionType from "#/types/ActionType";
import { initializeAgent } from "./agent";
import { Settings, saveSettings } from "./settings";
import Socket from "./socket";

const sendSpy = vi.spyOn(Socket, "send");

describe("initializeAgent", () => {
  it("Should initialize the agent with the current settings", () => {
    const settings: Settings = {
      LLM_MODEL: "llm_value",
      AGENT: "agent_value",
      LANGUAGE: "language_value",
      LLM_API_KEY: "sk-...",
    };

    const event = {
      action: ActionType.INIT,
      args: settings,
    };

    saveSettings(settings);
    initializeAgent();

    expect(sendSpy).toHaveBeenCalledWith(JSON.stringify(event));
  });
});
