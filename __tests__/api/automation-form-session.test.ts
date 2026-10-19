import { beforeEach, describe, expect, it } from "vitest";

import {
  getAutomationFormSession,
  initializeAutomationFormSession,
  patchAutomationFormSession,
} from "#/api/automation-form-session";

const BUNDLE_PATH =
  "oh-internal://uploads/97b19046-c2fb-4846-af9b-f596218b100e";

describe("automation form session", () => {
  beforeEach(() => {
    window.sessionStorage.clear();
  });

  it("keeps the existing custom bundle path when the draft is initialized", () => {
    initializeAutomationFormSession("conv-1", {
      prompt: "",
      kind: "custom",
      editingAutomationId: "automation-1",
      existingCustomTarballPath: BUNDLE_PATH,
    });

    expect(getAutomationFormSession("conv-1")?.existingCustomTarballPath).toBe(
      BUNDLE_PATH,
    );
  });

  it("keeps the existing custom bundle path after a field is edited", () => {
    initializeAutomationFormSession("conv-1", {
      prompt: "",
      kind: "custom",
      editingAutomationId: "automation-1",
      existingCustomTarballPath: BUNDLE_PATH,
      form: { kind: "custom", entrypoint: "python3 main.py" },
    });

    patchAutomationFormSession(
      "conv-1",
      { customSchedule: "0 7 * * 1-5" },
      { source: "user" },
    );

    expect(getAutomationFormSession("conv-1")?.existingCustomTarballPath).toBe(
      BUNDLE_PATH,
    );
  });
});
