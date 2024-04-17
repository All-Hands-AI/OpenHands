import { mergeAndUpdateSettings } from "./settingsService";
import { ArgConfigType } from "../types/ConfigType";

describe("mergeAndUpdateSettings", () => {
  it("should return initial settings if newSettings is empty", () => {
    const oldSettings = { key1: "value1" };
    const isInit = false;

    const result = mergeAndUpdateSettings({}, oldSettings, isInit);

    expect(result.mergedSettings).toEqual(oldSettings);
    expect(result.updatedSettings).toEqual({});
  });

  it("should add new keys to mergedSettings and updatedSettings", () => {
    const oldSettings = { key1: "value1" };
    const newSettings = { key2: "value2" };
    const isInit = false;

    const result = mergeAndUpdateSettings(newSettings, oldSettings, isInit);

    expect(result.mergedSettings).toEqual({
      key1: "value1",
      key2: "value2",
    });
    expect(result.updatedSettings).toEqual({
      key2: "value2", // New key
    });
  });

  it("should overwrite non-DISPLAY_MAP keys in mergedSettings", () => {
    const oldSettings = { key1: "value1" };
    const newSettings = { key1: "newvalue1" };
    const isInit = false;

    const result = mergeAndUpdateSettings(newSettings, oldSettings, isInit);

    expect(result.mergedSettings).toEqual({ key1: "newvalue1" });
    expect(result.updatedSettings).toEqual({});
  });

  it("should keep old values in mergedSettings if they are equal", () => {
    const oldSettings = {
      [ArgConfigType.LLM_MODEL]: "gpt-4-0125-preview",
      [ArgConfigType.AGENT]: "MonologueAgent",
    };
    const newSettings = {
      [ArgConfigType.AGENT]: "MonologueAgent",
    };
    const isInit = false;

    const result = mergeAndUpdateSettings(newSettings, oldSettings, isInit);

    expect(result.mergedSettings).toEqual(oldSettings);
    expect(result.updatedSettings).toEqual({});
  });

  it("should keep old values in mergedSettings if isInit is true and old value is not empty", () => {
    const oldSettings = {
      [ArgConfigType.LLM_MODEL]: "gpt-4-0125-preview",
      [ArgConfigType.AGENT]: "MonologueAgent",
    };
    const newSettings = {
      [ArgConfigType.AGENT]: "MonologueAgent",
    };
    const isInit = true;

    const result = mergeAndUpdateSettings(newSettings, oldSettings, isInit);

    expect(result.mergedSettings).toEqual(oldSettings);
    expect(result.updatedSettings).toEqual({});
  });

  it("should update mergedSettings, updatedSettings and set needToSend to true for relevant changes", () => {
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
    const isInit = false;

    const result = mergeAndUpdateSettings(newSettings, oldSettings, isInit);

    expect(result.mergedSettings).toEqual({
      [ArgConfigType.LLM_MODEL]: "gpt-4-0125-preview",
      [ArgConfigType.AGENT]: "CodeActAgent", // Updated value
      [ArgConfigType.LANGUAGE]: "es", // New key added
      key1: "newvalue1", // Updated value
      key2: "value2", // New key added
    });
    expect(result.updatedSettings).toEqual({
      [ArgConfigType.AGENT]: "CodeActAgent",
      [ArgConfigType.LANGUAGE]: "es",
      key2: "value2",
    });
    expect(result.needToSend).toBe(true);
  });
});
