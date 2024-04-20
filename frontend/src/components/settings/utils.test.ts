import { isDifferent } from "./utils";

describe("isDifferent", () => {
  const a = {
    key1: "value1",
    key2: "value2",
  };

  const b = {
    key1: "value1",
    key2: "value3",
  };

  it("should return true if the objects are different", () => {
    expect(isDifferent(a, b)).toBe(true);
  });

  it("should return false if the objects are the same", () => {
    expect(isDifferent(a, { ...a })).toBe(false);
    expect(isDifferent(a, a)).toBe(false);
  });
});
