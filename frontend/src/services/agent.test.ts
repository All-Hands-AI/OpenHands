import { describe, it, expect, vi } from "vitest";

import ActionType from "#/types/ActionType";
import { Settings } from "./settings";
import { initializeAgent } from "./agent";
import Socket from "./socket";
import store from "#/store";
import { setInitialized } from "#/state/taskSlice";

const sendSpy = vi.spyOn(Socket, "send");
const dispatchSpy = vi.spyOn(store, "dispatch");

describe("initializeAgent", () => {
  it("Should initialize the agent with the current settings", () => {
    const settings: Settings = {
      LLM_MODEL: "llm_value",
      AGENT: "agent_value",
      LANGUAGE: "language_value",
    };

    const event = {
      action: ActionType.INIT,
      args: settings,
    };

    initializeAgent(settings);

    expect(sendSpy).toHaveBeenCalledWith(JSON.stringify(event));
    expect(dispatchSpy).toHaveBeenCalledWith(setInitialized(false));
  });
});
