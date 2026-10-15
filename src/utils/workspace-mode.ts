import type { BackendKind } from "#/api/backend-registry/types";
import type { WorkspaceMode } from "#/api/conversation-metadata-store";
import { I18nKey } from "#/i18n/declaration";

export const DEFAULT_WORKSPACE_MODE: WorkspaceMode = "local_repo";

const HOST_WORKSPACE_MODES: WorkspaceMode[] = ["local_repo", "new_worktree"];

/**
 * The modes the launcher offers; Docker only when the server can run it.
 * Without a workspace there is no repo to work in or branch, so the only
 * choice left is where the conversation runs.
 */
export function getWorkspaceModeOptions(
  dockerSelectable: boolean,
  hasWorkspace = true,
): WorkspaceMode[] {
  if (!hasWorkspace) {
    return dockerSelectable ? ["local_repo", "docker_container"] : [];
  }
  return dockerSelectable
    ? [...HOST_WORKSPACE_MODES, "docker_container"]
    : HOST_WORKSPACE_MODES;
}

/**
 * The mode the launcher starts on: the Settings → Runtime default
 * (`conversation_settings.conversation_runtime`) when set, else the last one
 * used. A local default keeps the last host mode (repo or worktree).
 */
export function getDefaultWorkspaceMode(
  defaultRuntime: unknown,
  lastUsed: WorkspaceMode,
): WorkspaceMode {
  if (defaultRuntime === "docker") return "docker_container";
  if (defaultRuntime === "local" && lastUsed === "docker_container") {
    return DEFAULT_WORKSPACE_MODE;
  }
  return lastUsed;
}

export const LAST_LOCAL_WORKSPACE_MODE_STORAGE_KEY =
  "openhands-last-local-workspace-mode";

function isWorkspaceMode(value: string | null): value is WorkspaceMode {
  return (
    value === "local_repo" ||
    value === "new_worktree" ||
    value === "docker_container"
  );
}

export function readStoredLocalWorkspaceMode(): WorkspaceMode {
  if (typeof window === "undefined") return DEFAULT_WORKSPACE_MODE;

  try {
    const stored = window.localStorage.getItem(
      LAST_LOCAL_WORKSPACE_MODE_STORAGE_KEY,
    );
    return isWorkspaceMode(stored) ? stored : DEFAULT_WORKSPACE_MODE;
  } catch {
    return DEFAULT_WORKSPACE_MODE;
  }
}

export function writeStoredLocalWorkspaceMode(mode: WorkspaceMode): void {
  if (typeof window === "undefined") return;

  try {
    window.localStorage.setItem(LAST_LOCAL_WORKSPACE_MODE_STORAGE_KEY, mode);
  } catch {
    // Ignore storage failures; the selector still works for this render.
  }
}

export function getWorkspaceModeI18nKey(
  mode: WorkspaceMode,
  backendKind: BackendKind,
  hasWorkspace = true,
): I18nKey {
  if (mode === "new_worktree") {
    return I18nKey.COMMON$WORKSPACE_MODE_NEW_WORKTREE;
  }
  if (mode === "docker_container") {
    return I18nKey.COMMON$WORKSPACE_MODE_DOCKER_CONTAINER;
  }
  if (!hasWorkspace) return I18nKey.COMMON$WORKSPACE_MODE_LOCAL;
  return backendKind === "cloud"
    ? I18nKey.COMMON$WORKSPACE_MODE_CLOUD_REPO
    : I18nKey.COMMON$WORKSPACE_MODE_LOCAL_REPO;
}
