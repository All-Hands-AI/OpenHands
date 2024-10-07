/**
 * Parses the raw output from the terminal into the command and symbol
 * @param raw The raw output to be displayed in the terminal
 * @returns The parsed output
 *
 * @example
 * const raw =
 *  "web_scraper.py\r\n\r\n[Python Interpreter: /openhands/poetry/openhands-5O4_aCHf-py3.12/bin/python]\nopenhands@659478cb008c:/workspace $ ";
 *
 * const parsed = parseTerminalOutput(raw);
 *
 * console.log(parsed.output); // web_scraper.py
 * console.log(parsed.symbol); // openhands@659478cb008c:/workspace $
 */
export const parseTerminalOutput = (raw: string) => {
  const envRegex = /(.*)\[Python Interpreter: (.*)\]/s;
  const match = raw.match(envRegex);

  if (!match) return raw;
  return match[1]?.trim() || "";
};
