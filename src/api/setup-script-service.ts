import {
  ConversationClient,
  FileClient,
  ServerClient,
} from "@openhands/typescript-client/clients";
import { getAgentServerWorkingDir } from "./agent-server-config";
import { getAgentServerClientOptions } from "./agent-server-client-options";
import { getEffectiveLocalBackend } from "./backend-registry/active-store";
import {
  getCachedAgentServerInfo,
  isSdkHttpStatusError,
} from "./agent-server-compatibility";

/**
 * Workspace-relative path of the bootstrap script. Mirrors the convention the
 * Cloud/self-hosted app-server already honours; see OpenHands/enterprise#41.
 */
export const SETUP_SCRIPT_RELATIVE_PATH = ".openhands/setup.sh";

/**
 * Capability the agent-server advertises when it exposes
 * `POST /api/conversations/{id}/execute_tool` (software-agent-sdk#6099).
 *
 * Gated on the capability rather than a version floor: the route ships in the
 * same package version as servers that predate it, so a version compare cannot
 * distinguish them.
 */
export const DIRECT_TOOL_EXECUTION_CAPABILITY = "direct_tool_execution_v1";

const SETUP_SCRIPT_DETECT_TIMEOUT_MS = 5000;
const SETUP_SCRIPT_EXECUTE_TIMEOUT_MS = 600_000;
const SETUP_SCRIPT_BUSY_STATUS = 409;
const SETUP_SCRIPT_BUSY_RETRY_DELAY_MS = 1000;
const SETUP_SCRIPT_BUSY_MAX_ATTEMPTS = 60;

interface ObservationTextContent {
  type: "text";
  text: string;
}

/** The subset of the agent-server's `TerminalObservation` this service reads. */
export interface TerminalObservation {
  kind: string;
  command?: string | null;
  exit_code?: number | null;
  timeout?: boolean;
  is_error?: boolean;
  content?: Array<ObservationTextContent | { type: string }>;
  [key: string]: unknown;
}

/**
 * The slice of the typescript-client `ConversationClient` this service drives.
 *
 * `executeTool` is not in the published `@openhands/typescript-client` yet (it
 * ships in OpenHands/software-agent-sdk#6099); narrowing to this local interface
 * keeps `tsc` and `eslint` green until the client is republished, at which
 * point the cast below can be dropped. Same pattern as
 * `plugins-management-service.ts`.
 */
interface DirectToolClient {
  executeTool(
    conversationId: string,
    request: {
      tool_name: string;
      action: { kind: string; [key: string]: unknown };
    },
  ): Promise<{ observation: TerminalObservation }>;
}

export type SetupScriptSkipReason =
  | "no-backend"
  | "unsupported-capability"
  | "no-script";

/** A detected setup script, ready to run once the conversation exists. */
export interface SetupScriptPlan {
  workingDir: string;
  scriptPath: string;
  command: string;
}

/** Progress reported to the caller while the bootstrap runs. */
export type SetupScriptStatusUpdate =
  | { phase: "running" }
  | { phase: "succeeded" }
  | { phase: "failed"; exitCode: number | null; output: string }
  | { phase: "error"; message: string };

export type SetupScriptResult =
  | { status: "ran"; exitCode: number | null; output: string; failed: boolean }
  | { status: "skipped"; reason: SetupScriptSkipReason }
  | { status: "error"; message: string };

function getSetupScriptPath(workingDir: string): string {
  return `${workingDir.replace(/\/+$/, "")}/${SETUP_SCRIPT_RELATIVE_PATH}`;
}

function buildSetupCommand(scriptPath: string): string {
  // `.` (POSIX source) rather than `source`: the terminal shell may be dash,
  // where `source` is not found — the exact failure behind enterprise#41.
  // Sourcing keeps `export`/`cd` in the agent's own terminal session, which is
  // the whole point of routing this through the tool executor.
  return `chmod +x "${scriptPath}" && . "${scriptPath}"`;
}

function extractText(observation: TerminalObservation): string {
  const content = observation.content ?? [];
  return content
    .filter(
      (item): item is ObservationTextContent =>
        item.type === "text" &&
        typeof (item as ObservationTextContent).text === "string",
    )
    .map((item) => item.text)
    .join("\n")
    .trim();
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}

/**
 * Runs `<workspace>/.openhands/setup.sh` through the conversation's own
 * terminal, so the environment it sets survives into the agent's later
 * commands. Local backends only: on Cloud the app-server owns this (see
 * OpenHands/enterprise#41) and the agent-server has no such route.
 *
 * Mirrors `HooksService`: degrade to "skip" whenever the backend is cloud, has
 * no backend, or the agent-server does not advertise direct tool execution.
 */
class SetupScriptService {
  static isDirectToolExecutionSupported(
    info: { capabilities?: string[] } | null | undefined,
  ): boolean {
    return Boolean(
      info &&
      Array.isArray(info.capabilities) &&
      info.capabilities.includes(DIRECT_TOOL_EXECUTION_CAPABILITY),
    );
  }

  /**
   * Capabilities come from the Canvas server-info cache when a probe already
   * populated it, otherwise straight from `GET /api/server_info`. The adapter's
   * own `fetchBackendServerInfo` deliberately does not fill that cache, so
   * trusting the cache alone would silently disable setup.
   */
  private static async resolveDirectToolExecutionSupport(): Promise<boolean> {
    const cached = getCachedAgentServerInfo();
    if (cached) {
      return this.isDirectToolExecutionSupported(cached);
    }
    try {
      const info = await new ServerClient(
        getAgentServerClientOptions({
          timeout: SETUP_SCRIPT_DETECT_TIMEOUT_MS,
        }),
      ).getServerInfo();
      return this.isDirectToolExecutionSupported(info);
    } catch {
      return false;
    }
  }

  private static async scriptExists(
    workingDir: string,
    scriptPath: string,
  ): Promise<boolean> {
    try {
      await new FileClient(
        getAgentServerClientOptions({
          workingDir,
          timeout: SETUP_SCRIPT_DETECT_TIMEOUT_MS,
        }),
      ).downloadTextFile(scriptPath);
      return true;
    } catch (error) {
      if (!isSdkHttpStatusError(error, 404)) {
        console.warn(
          "Could not check for .openhands/setup.sh; skipping setup:",
          error,
        );
      }
      return false;
    }
  }

  /**
   * Detect the script before the conversation is created, so the caller can
   * withhold the initial message until setup has run. Returns null — and logs
   * why — when setup does not apply.
   */
  static async prepare(workingDir?: string): Promise<SetupScriptPlan | null> {
    if (!getEffectiveLocalBackend()) {
      return null;
    }

    const resolvedWorkingDir = workingDir ?? getAgentServerWorkingDir();
    const scriptPath = getSetupScriptPath(resolvedWorkingDir);
    const [supported, exists] = await Promise.all([
      this.resolveDirectToolExecutionSupport(),
      this.scriptExists(resolvedWorkingDir, scriptPath),
    ]);

    if (!supported) {
      console.info(
        "Agent server does not advertise direct tool execution; skipping .openhands/setup.sh.",
      );
      return null;
    }
    if (!exists) {
      return null;
    }

    return {
      workingDir: resolvedWorkingDir,
      scriptPath,
      command: buildSetupCommand(scriptPath),
    };
  }

  /**
   * Run a prepared script through the conversation's terminal. Never throws:
   * a failed script, a missing route, or a conversation that stays busy all
   * resolve to a result the caller reports while still starting the agent.
   *
   * `onProgress` is invoked around the call so the caller can surface a
   * non-blocking "setting up workspace" state.
   */
  static async run(
    plan: SetupScriptPlan,
    conversationId: string,
    onProgress?: (update: SetupScriptStatusUpdate) => void,
  ): Promise<SetupScriptResult> {
    const client = new ConversationClient(
      getAgentServerClientOptions({ timeout: SETUP_SCRIPT_EXECUTE_TIMEOUT_MS }),
    ) as unknown as DirectToolClient;

    onProgress?.({ phase: "running" });

    for (
      let attempt = 0;
      attempt < SETUP_SCRIPT_BUSY_MAX_ATTEMPTS;
      attempt += 1
    ) {
      try {
        const { observation } = await client.executeTool(conversationId, {
          tool_name: "terminal",
          action: { kind: "TerminalAction", command: plan.command },
        });
        const exitCode = observation.exit_code ?? null;
        const output = extractText(observation);
        const failed = exitCode !== 0;
        if (failed) {
          onProgress?.({ phase: "failed", exitCode, output });
        } else {
          onProgress?.({ phase: "succeeded" });
        }
        return { status: "ran", exitCode, output, failed };
      } catch (error) {
        if (isSdkHttpStatusError(error, SETUP_SCRIPT_BUSY_STATUS)) {
          await sleep(SETUP_SCRIPT_BUSY_RETRY_DELAY_MS);
          continue;
        }
        const message = error instanceof Error ? error.message : String(error);
        onProgress?.({ phase: "error", message });
        return { status: "error", message };
      }
    }

    const message = "Setup script did not run: the conversation stayed busy.";
    onProgress?.({ phase: "error", message });
    return { status: "error", message };
  }
}

export default SetupScriptService;
