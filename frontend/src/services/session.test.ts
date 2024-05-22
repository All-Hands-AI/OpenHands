import { describe, expect, it, vi } from "vitest";

import ActionType from "#/types/ActionType";
import { Settings, saveSettings } from "./settings";
import Session from "./session";

const sendSpy = vi.spyOn(Session, "send");
const setupSpy = vi
  /* eslint-disable-next-line @typescript-eslint/no-explicit-any */
  .spyOn(Session as any, "_setupSocket")
  .mockImplementation(() => {
    /* eslint-disable-next-line @typescript-eslint/dot-notation */
    Session["_initializeAgent"](); // use key syntax to fix complaint about private fn
  });

describe("startNewSession", () => {
  it("Should start a new session with the current settings", () => {
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
    Session.startNewSession();

    expect(setupSpy).toHaveBeenCalledTimes(1);
    expect(sendSpy).toHaveBeenCalledWith(JSON.stringify(event));
  });
});
