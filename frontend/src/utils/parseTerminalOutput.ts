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
  const envRegex = /\[Python Interpreter: (.*)\]/;
  const env = raw.match(envRegex);
  let fullOutput = raw;
  if (env && env[0]) fullOutput = fullOutput.replace(`${env[0]}\n`, "");
  const [output, s] = fullOutput.split("\r\n\r\n");
  const symbol = s || "$";

  return {
    output: output.trim(),
    symbol: symbol.trim(),
  };
};
