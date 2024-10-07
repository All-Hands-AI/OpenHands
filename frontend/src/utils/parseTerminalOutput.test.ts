import { describe, it, expect } from "vitest";
import { parseTerminalOutput } from "./parseTerminalOutput";

describe("parseTerminalOutput", () => {
  it("should parse the command, env, and symbol", () => {
    const raw =
      "web_scraper.py\r\n\r\n[Python Interpreter: /openhands/poetry/openhands-5O4_aCHf-py3.12/bin/python]\nopenhands@659478cb008c:/workspace $ ";

    const parsed = parseTerminalOutput(raw);

    expect(parsed.output).toBe("web_scraper.py");
    expect(parsed.symbol).toBe("openhands@659478cb008c:/workspace $");
  });

  it("should return raw output if unable to parse", () => {
    const raw = "web_scraper.py";

    const parsed = parseTerminalOutput(raw);
    expect(parsed.output).toBe("web_scraper.py");
  });
});
