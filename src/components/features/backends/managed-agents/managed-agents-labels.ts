import type { TFunction } from "i18next";

import type {
  MarsAgentConfig,
  MarsSession,
  MarsSessionPhase,
} from "#/api/mars/mars-tunnel-backend";
import type { MarsConnectStage } from "#/hooks/use-connect-mars-session";
import { I18nKey } from "#/i18n/declaration";

const SHORT_ID_LENGTH = 8;

export const PHASE_DOT_CLASS: Record<MarsSessionPhase, string> = {
  ready: "bg-status-success ring-3 ring-status-success/22",
  paused: "bg-warning",
  starting: "bg-interactive-selected animate-pulse",
  failed: "bg-status-error",
  ended: "bg-text-tertiary",
};

export const PHASE_LABEL_KEY: Record<MarsSessionPhase, I18nKey> = {
  ready: I18nKey.COMMON$RUNNING,
  paused: I18nKey.COMMON$PAUSED,
  starting: I18nKey.COMMON$STARTING,
  failed: I18nKey.DO_AGENTS$STATUS_FAILED,
  ended: I18nKey.DO_AGENTS$STATUS_ENDED,
};

export const STAGE_LABEL_KEY: Record<MarsConnectStage, I18nKey> = {
  waking: I18nKey.DO_AGENTS$STAGE_WAKING,
  tunnel: I18nKey.DO_AGENTS$STAGE_TUNNEL,
  agent: I18nKey.DO_AGENTS$STAGE_AGENT,
};

/** Separates agent and session in a registered backend's display name. */
const BACKEND_NAME_SEPARATOR = " · ";

export function shortSessionId(session: MarsSession): string {
  return session.session_id.slice(0, SHORT_ID_LENGTH);
}

export function agentLabel(config: MarsAgentConfig): string {
  return config.name?.trim() || config.id;
}

export function getSessionDisplayName(
  session: MarsSession,
  t: TFunction<"openhands">,
): string {
  return (
    session.name?.trim() ||
    t(I18nKey.DO_AGENTS$SESSION_NAME_FALLBACK, { id: shortSessionId(session) })
  );
}

/** "<agent> · <session>" so the backend selector names both. */
export function buildMarsBackendName(
  session: MarsSession,
  config: MarsAgentConfig | undefined,
  t: TFunction<"openhands">,
): string {
  const sessionName = getSessionDisplayName(session, t);
  return config
    ? `${agentLabel(config)}${BACKEND_NAME_SEPARATOR}${sessionName}`
    : sessionName;
}
