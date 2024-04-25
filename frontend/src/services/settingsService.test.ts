import { ArgConfigType } from "#/types/ConfigType";
import { getSettingOrDefault, getUpdatedSettings } from "./settingsService";

Storage.prototype.getItem = vi.fn();

describe("getSettingOrDefault", () => {
  it("should return the value from localStorage if it exists", () => {
    (localStorage.getItem as jest.Mock).mockReturnValue("value");
    const result = getSettingOrDefault("some_key");

    expect(result).toEqual("value");
  });

  it("should return the default value if localStorage does not exist", () => {
    (localStorage.getItem as jest.Mock).mockReturnValue(null);
    const result = getSettingOrDefault("LLM_MODEL");

    expect(result).toEqual("gpt-3.5-turbo");
  });
});

describe("getUpdatedSettings", () => {
  it("should return initial settings if newSettings is empty", () => {
    const oldSettings = { key1: "value1" };

    const result = getUpdatedSettings({}, oldSettings);

    expect(result).toStrictEqual({});
  });

  it("should update settings", () => {
    const oldSettings = {
      [ArgConfigType.LLM_MODEL]: "gpt-4-0125-preview",
      [ArgConfigType.AGENT]: "MonologueAgent",
      [ArgConfigType.LANGUAGE]: "en",
    };
    const newSettings = {
      [ArgConfigType.AGENT]: "OtherAgent",
    };

    const result = getUpdatedSettings(newSettings, oldSettings);

    expect(result).toStrictEqual({
      [ArgConfigType.AGENT]: "OtherAgent",
    });
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

    expect(result).toStrictEqual({});
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

    expect(result).toStrictEqual({
      [ArgConfigType.AGENT]: "CodeActAgent",
      [ArgConfigType.LANGUAGE]: "es",
    });
  });

  it("should not update settings that are not supported", () => {
    const oldSettings = {
      [ArgConfigType.LLM_MODEL]: "gpt-4-0125-preview",
      [ArgConfigType.AGENT]: "MonologueAgent",
    };
    const newSettings = {
      [ArgConfigType.LLM_MODEL]: "gpt-4-0125-preview",
      [ArgConfigType.AGENT]: "CodeActAgent",
      key1: "newvalue1",
      key2: "value2",
    };

    const result = getUpdatedSettings(newSettings, oldSettings);

    expect(result).toStrictEqual({
      [ArgConfigType.AGENT]: "CodeActAgent",
    });
  });
});
