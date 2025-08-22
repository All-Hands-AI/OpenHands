/**
 * Unified terminal output processing utility
 * Consolidates all terminal output processing logic in one place
 */

interface ProcessingOptions {
  isFirstChunk?: boolean;
  removeCommandPrefix?: string;
}

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
 * Removes command prefix from output (used for first chunk)
 */
const removeCommandPrefix = (output: string, command: string): string => {
  // Remove the command from the beginning of the output if it appears there
  const lines = output.split("\n");
  if (lines.length > 0 && lines[0].trim() === command.trim()) {
    return lines.slice(1).join("\n");
  }
  return output;
};

/**
 * Converts line endings for proper terminal display
 */
const convertLineEndings = (content: string): string =>
  content.replaceAll("\n", "\r\n");

/**
 * Processes raw terminal output by applying all necessary transformations
 * @param raw The raw output from the terminal
 * @param options Processing options
 * @returns The processed output ready for display
 */
export const processTerminalOutput = (
  raw: string,
  options: ProcessingOptions = {},
): string => {
  let processed = raw;

  // Remove Python interpreter info if present
  processed = removePythonInterpreterInfo(processed);

  // Remove command prefix if this is the first chunk
  if (options.isFirstChunk && options.removeCommandPrefix) {
    processed = removeCommandPrefix(processed, options.removeCommandPrefix);
  }

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
