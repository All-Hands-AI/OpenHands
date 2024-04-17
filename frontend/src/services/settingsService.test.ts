import { getUpdatedSettings } from "./settingsService";
import { ArgConfigType } from "../types/ConfigType";

describe("mergeAndUpdateSettings", () => {
  it("should return initial settings if newSettings is empty", () => {
    const oldSettings = { key1: "value1" };

    const result = getUpdatedSettings({}, oldSettings);

    expect(result).toEqual({});
  });

  it("should add new keys to updatedSettings", () => {
    const oldSettings = { key1: "value1" };
    const newSettings = { key2: "value2" };

    const result = getUpdatedSettings(newSettings, oldSettings);

    expect(result).toEqual({
      key2: "value2", // New key
    });
  });

  it("should overwrite non-DISPLAY_MAP keys in mergedSettings", () => {
    const oldSettings = { key1: "value1" };
    const newSettings = { key1: "newvalue1" };

    const result = getUpdatedSettings(newSettings, oldSettings);

    expect(result).toEqual({});
  });

  it("should show no values if they are equal", () => {
    const oldSettings = {
      [ArgConfigType.LLM_MODEL]: "gpt-4-0125-preview",
      [ArgConfigType.AGENT]: "MonologueAgent",
    };
    const newSettings = {
      [ArgConfigType.AGENT]: "MonologueAgent",
    };

    const result = getUpdatedSettings(newSettings, oldSettings);

    expect(result).toEqual({});
  });

  it("should update all settings", () => {
    const oldSettings = {
      [ArgConfigType.LLM_MODEL]: "gpt-4-0125-preview",
      [ArgConfigType.AGENT]: "MonologueAgent",
      key1: "value1",
    };
    const newSettings = {
      [ArgConfigType.AGENT]: "CodeActAgent",
      [ArgConfigType.LANGUAGE]: "es",
      key1: "newvalue1",
      key2: "value2",
    };

    const result = getUpdatedSettings(newSettings, oldSettings);

    expect(result).toEqual({
      [ArgConfigType.AGENT]: "CodeActAgent",
      [ArgConfigType.LANGUAGE]: "es",
      key2: "value2",
    });
  });
});
