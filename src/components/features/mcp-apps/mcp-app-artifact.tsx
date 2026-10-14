import React from "react";
import { AppWindow, RefreshCw, TriangleAlert } from "lucide-react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { BrandButton } from "#/components/features/settings/brand-button";
import { cn } from "#/utils/utils";
import type { ObservationEvent } from "#/types/agent-server/core";
import type { MCPToolObservation } from "#/types/agent-server/core/base/observation";
import type {
  MCPAppBinding,
  MCPAppDescriptor,
  MCPAppSession,
} from "#/types/mcp-app";
import { useMCPAppHost } from "./mcp-app-host-context";
import styles from "./mcp-app-artifact.module.css";

const INITIAL_FRAME_HEIGHT = 360;
const MIN_FRAME_HEIGHT = 160;
const MAX_FRAME_HEIGHT = 1200;
const APP_LOAD_TIMEOUT_MS = 30_000;

type AppStatus = "loading" | "ready" | "error";

interface MCPAppArtifactProps {
  event: ObservationEvent<MCPToolObservation>;
  descriptor: MCPAppDescriptor;
}

/** The visualizer owns the original text; this component owns only the App. */
// @spec MCA-003 — Load the App through an explicitly installed Host adapter.
export function MCPAppArtifact({ event, descriptor }: MCPAppArtifactProps) {
  const { t } = useTranslation("openhands");
  const { host, scope } = useMCPAppHost();
  const currentHost = React.useRef({ host, scope });
  React.useLayoutEffect(() => {
    currentHost.current = { host, scope };
  }, [host, scope]);
  const iframeRef = React.useRef<HTMLIFrameElement>(null);
  const [status, setStatus] = React.useState<AppStatus>("loading");
  const [height, setHeight] = React.useState(INITIAL_FRAME_HEIGHT);
  const [attempt, setAttempt] = React.useState(0);

  const isPlanningEvent =
    "isFromPlanningAgent" in event && event.isFromPlanningAgent === true;
  const owner = isPlanningEvent
    ? (scope?.planningConversationId ?? null)
    : (scope?.conversationId ?? null);
  const backendId = scope?.backendId;
  const orgId = scope?.orgId ?? null;
  const revision = scope?.connectionRevision;
  const readOnly = scope ? (scope.readOnly ?? false) : true;

  React.useEffect(() => {
    const iframe = iframeRef.current;
    if (
      !host ||
      !owner ||
      !backendId ||
      revision === undefined ||
      readOnly ||
      !iframe
    ) {
      return undefined;
    }

    const controller = new AbortController();
    let session: MCPAppSession | null = null;
    let bridge: { dispose: () => Promise<void> } | null = null;
    setStatus("loading");
    setHeight(INITIAL_FRAME_HEIGHT);

    const binding: MCPAppBinding = {
      backendId,
      orgId,
      connectionRevision: revision,
      ownerConversationId: owner,
      eventId: event.id,
      actionId: event.action_id,
      toolCallId: event.tool_call_id,
      toolName: event.tool_name,
      resourceUri: descriptor.resourceUri,
    };

    // @spec MCA-004 — A View stays bound to its origin, including after a mode switch.
    const isWritable = () => {
      const current = currentHost.current;
      return (
        !controller.signal.aborted &&
        current.host === host &&
        current.scope?.backendId === backendId &&
        current.scope.orgId === orgId &&
        current.scope.connectionRevision === revision &&
        !current.scope.readOnly &&
        current.scope.writableConversationId === owner
      );
    };

    const dispose = async () => {
      window.clearTimeout(loadTimeout);
      const mounted = bridge;
      const opened = session;
      bridge = null;
      session = null;
      try {
        await mounted?.dispose();
      } finally {
        await opened?.dispose?.();
      }
    };

    const fail = () => {
      if (controller.signal.aborted) return;
      setStatus("error");
      controller.abort();
      iframe.removeAttribute("src");
      void dispose().catch(() => undefined);
    };

    const loadTimeout = window.setTimeout(fail, APP_LOAD_TIMEOUT_MS);

    const load = async () => {
      try {
        const sandbox = new URL(host.sandboxUrl);
        if (
          (sandbox.protocol !== "http:" && sandbox.protocol !== "https:") ||
          sandbox.origin === window.location.origin ||
          sandbox.username ||
          sandbox.password
        ) {
          throw new Error("Invalid MCP App sandbox origin");
        }
        const opened = await host.open(binding, { signal: controller.signal });
        if (controller.signal.aborted) {
          await opened.dispose?.();
          return;
        }
        session = opened;
        const resource = await opened.readResource(descriptor.resourceUri, {
          signal: controller.signal,
        });
        if (controller.signal.aborted) return;

        // Keep the protocol SDK out of the ordinary conversation's eager graph.
        const { mountMCPAppBridge } = await import("./mcp-app-bridge");
        if (controller.signal.aborted) return;
        const mounted = await mountMCPAppBridge({
          iframe,
          sandboxUrl: sandbox.href,
          descriptor,
          resource,
          session: opened,
          signal: controller.signal,
          isWritable,
          onReady: () => {
            if (!controller.signal.aborted) {
              window.clearTimeout(loadTimeout);
              setStatus("ready");
            }
          },
          onError: fail,
          onSizeChange: (requestedHeight) => {
            if (
              !controller.signal.aborted &&
              Number.isFinite(requestedHeight)
            ) {
              setHeight(
                Math.max(
                  MIN_FRAME_HEIGHT,
                  Math.min(MAX_FRAME_HEIGHT, requestedHeight),
                ),
              );
            }
          },
        });
        if (controller.signal.aborted) {
          await mounted.dispose();
          return;
        }
        bridge = mounted;
      } catch {
        fail();
      }
    };
    void load();

    return () => {
      controller.abort();
      void dispose().catch(() => undefined);
      iframe.removeAttribute("src");
    };
  }, [
    host,
    owner,
    backendId,
    orgId,
    revision,
    readOnly,
    attempt,
    event.id,
    event.action_id,
    event.tool_call_id,
    event.tool_name,
    descriptor.resourceUri,
    descriptor.toolInput,
    descriptor.toolResult,
  ]);

  if (!host || !owner || !backendId || readOnly) {
    return (
      <div
        role="status"
        className="flex min-w-0 items-start gap-3 rounded-lg border border-border-subtle bg-surface px-4 py-3"
      >
        <AppWindow aria-hidden className="mt-0.5 size-4 shrink-0 text-muted" />
        <p className="text-pretty text-sm leading-6 text-text-secondary">
          {t(I18nKey.MCP$APP_UNAVAILABLE)}
        </p>
      </div>
    );
  }

  return (
    <div
      className={cn(
        "min-w-0 overflow-hidden rounded-lg border border-border-subtle bg-surface",
        status !== "ready" && "p-4",
      )}
    >
      {status === "loading" && (
        <div role="status" className="flex flex-col gap-4">
          <p className="text-pretty text-sm leading-6 text-text-secondary">
            {t(I18nKey.MCP$APP_LOADING)}
          </p>
          <div aria-hidden className="flex flex-col gap-3">
            <div className="h-4 w-1/3 rounded bg-surface-raised" />
            <div className="h-8 w-1/4 rounded bg-surface-raised" />
            <div className="h-24 rounded bg-surface-raised" />
            <div className="flex gap-2">
              <div className="h-8 w-1/4 rounded bg-surface-raised" />
              <div className="h-8 w-1/3 rounded bg-surface-raised" />
            </div>
          </div>
        </div>
      )}
      {status === "error" && (
        <div
          role="alert"
          className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"
        >
          <div className="flex min-w-0 items-start gap-3">
            <TriangleAlert
              aria-hidden
              className="mt-0.5 size-4 shrink-0 text-feedback-error"
            />
            <p className="text-pretty text-sm leading-6 text-text-secondary">
              {t(I18nKey.MCP$APP_ERROR)}
            </p>
          </div>
          <BrandButton
            type="button"
            variant="secondary"
            startContent={<RefreshCw aria-hidden className="size-4" />}
            className="shrink-0 self-start transition-none focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus sm:self-center"
            onClick={() => setAttempt((value) => value + 1)}
          >
            {t(I18nKey.LAUNCH$TRY_AGAIN)}
          </BrandButton>
        </div>
      )}
      <iframe
        ref={iframeRef}
        title={t(I18nKey.MCP$APP_TITLE)}
        sandbox="allow-scripts allow-same-origin"
        referrerPolicy="no-referrer"
        hidden={status !== "ready"}
        style={{ "--mcp-app-height": `${height}px` } as React.CSSProperties}
        className={cn(
          styles.frame,
          "w-full border-0",
          status === "ready" && "block",
        )}
      />
    </div>
  );
}
