import type { TFunction } from "i18next";
import { I18nKey } from "#/i18n/declaration";
import type {
  ExtendedMCPTestFailureKind,
  MCPServerType,
} from "#/types/mcp-server";

// Where an HTML document begins inside an error detail. Some MCP servers
// answer a failed request (such as dynamic client registration) with their
// web error page, and the backend passes the whole body through.
const HTML_DOCUMENT_START = /<!doctype html|<html[\s>]/i;

/** The detail up to an embedded HTML page, which is not readable as text. */
function withoutHtmlDocument(error: string): string {
  const match = HTML_DOCUMENT_START.exec(error);
  return match ? error.slice(0, match.index).trimEnd() : error;
}

/**
 * Kind-specific, localized guidance for a failed MCP connection test.
 * `error` is interpolated for the kinds whose message surfaces the provider
 * detail — callers pass display-safe (redacted) text. `serverType` picks
 * transport-appropriate copy for a `connection` failure: a stdio server has
 * no URL, its command failed to start. An unknown type reads as remote.
 */
export function makeMcpTestErrorMessage(
  t: TFunction<"openhands">,
  errorKind: ExtendedMCPTestFailureKind,
  error: string,
  serverType: MCPServerType | undefined,
): string {
  const detail = withoutHtmlDocument(error);
  switch (errorKind) {
    case "timeout":
      return t(I18nKey.MCP$TEST_ERROR_TIMEOUT);
    case "authorization":
      return t(I18nKey.MCP$TEST_ERROR_AUTHORIZATION);
    case "connection":
      return serverType === "stdio"
        ? t(I18nKey.MCP$TEST_ERROR_STDIO_START, { error: detail })
        : t(I18nKey.MCP$TEST_ERROR_CONNECTION, { error: detail });
    case "credentials":
      return t(I18nKey.MCP$TEST_ERROR_CREDENTIALS, { error: detail });
    default:
      return t(I18nKey.MCP$TEST_ERROR_UNKNOWN, { error: detail });
  }
}
