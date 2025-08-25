/**
 * Removes Python interpreter information from terminal output
 */
const removePythonInterpreterInfo = (raw: string): string => {
  const envRegex = /(.*)\[Python Interpreter: (.*)\]/s;
  const match = raw.match(envRegex);

  if (!match) return raw;
  return match[1]?.trim() || "";
};

/**
 * Converts line endings for proper terminal display
 */
const convertLineEndings = (content: string): string =>
  content.replaceAll("\n", "\r\n");

/**
 * Processes raw terminal output by applying all necessary transformations
 * @param raw The raw output from the terminal
 * @returns The processed output ready for display
 */
export const processTerminalOutput = (raw: string): string => {
  let processed = raw;

  // Remove Python interpreter info if present
  processed = removePythonInterpreterInfo(processed);

  // Convert line endings for terminal display
  processed = convertLineEndings(processed);

  return processed;
};

/**
 * Legacy function for backward compatibility
 * @deprecated Use processTerminalOutput instead
 */
export const parseTerminalOutput = (raw: string): string =>
  removePythonInterpreterInfo(raw);
