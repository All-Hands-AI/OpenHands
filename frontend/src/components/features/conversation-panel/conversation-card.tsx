import React from "react";
import { useSelector } from "react-redux";
import posthog from "posthog-js";
import { useTranslation } from "react-i18next";
import { formatTimeDelta } from "#/utils/format-time-delta";
import { ConversationRepoLink } from "./conversation-repo-link";
import { ConversationStateIndicator } from "./conversation-state-indicator";
import { EllipsisButton } from "./ellipsis-button";
import { ConversationCardContextMenu } from "./conversation-card-context-menu";
import { SystemMessageModal } from "./system-message-modal";
import { MicroagentsModal } from "./microagents-modal";
import { BudgetDisplay } from "./budget-display";
import { cn } from "#/utils/utils";
import { BaseModal } from "../../shared/modals/base-modal/base-modal";
import { RootState } from "#/store";
import { I18nKey } from "#/i18n/declaration";
import { transformVSCodeUrl } from "#/utils/vscode-url-helper";
import OpenHands from "#/api/open-hands";
import { useWsClient } from "#/context/ws-client-provider";
import { isSystemMessage } from "#/types/core/guards";
import { ConversationStatus } from "#/types/conversation-status";
import { RepositorySelection } from "#/api/open-hands.types";

interface ConversationCardProps {
  onClick?: () => void;
  onDelete?: () => void;
  onStop?: () => void;
  onChangeTitle?: (title: string) => void;
  showOptions?: boolean;
  isActive?: boolean;
  title: string;
  selectedRepository: RepositorySelection | null;
  lastUpdatedAt: string; // ISO 8601
  createdAt?: string; // ISO 8601
  conversationStatus?: ConversationStatus;
  variant?: "compact" | "default";
  conversationId?: string; // Optional conversation ID for VS Code URL
}

const MAX_TIME_BETWEEN_CREATION_AND_UPDATE = 1000 * 60 * 30; // 30 minutes

export function ConversationCard({
  onClick,
  onDelete,
  onStop,
  onChangeTitle,
  showOptions,
  isActive,
  title,
  selectedRepository,
  // lastUpdatedAt is kept in props for backward compatibility
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  lastUpdatedAt,
  createdAt,
  conversationStatus = "STOPPED",
  variant = "default",
  conversationId,
}: ConversationCardProps) {
  const { t } = useTranslation();
  const { parsedEvents } = useWsClient();
  const [contextMenuVisible, setContextMenuVisible] = React.useState(false);
  const [titleMode, setTitleMode] = React.useState<"view" | "edit">("view");
  const [metricsModalVisible, setMetricsModalVisible] = React.useState(false);
  const [systemModalVisible, setSystemModalVisible] = React.useState(false);
  const [microagentsModalVisible, setMicroagentsModalVisible] =
    React.useState(false);
  const inputRef = React.useRef<HTMLInputElement>(null);

  const systemMessage = parsedEvents.find(isSystemMessage);

  // Subscribe to metrics data from Redux store
  const metrics = useSelector((state: RootState) => state.metrics);

  const handleBlur = () => {
    if (inputRef.current?.value) {
      const trimmed = inputRef.current.value.trim();
      onChangeTitle?.(trimmed);
      inputRef.current!.value = trimmed;
    } else {
      // reset the value if it's empty
      inputRef.current!.value = title;
    }

    setTitleMode("view");
  };

  const handleKeyUp = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Enter") {
      event.currentTarget.blur();
    }
  };

  const handleInputClick = (event: React.MouseEvent<HTMLInputElement>) => {
    if (titleMode === "edit") {
      event.preventDefault();
      event.stopPropagation();
    }
  };

  const handleDelete = (event: React.MouseEvent<HTMLButtonElement>) => {
    event.preventDefault();
    event.stopPropagation();
    onDelete?.();
    setContextMenuVisible(false);
  };

  const handleStop = (event: React.MouseEvent<HTMLButtonElement>) => {
    event.preventDefault();
    event.stopPropagation();
    onStop?.();
    setContextMenuVisible(false);
  };

  const handleEdit = (event: React.MouseEvent<HTMLButtonElement>) => {
    event.preventDefault();
    event.stopPropagation();
    setTitleMode("edit");
    setContextMenuVisible(false);
  };

  const handleDownloadViaVSCode = async (
    event: React.MouseEvent<HTMLButtonElement>,
  ) => {
    event.preventDefault();
    event.stopPropagation();
    posthog.capture("download_via_vscode_button_clicked");

    // Fetch the VS Code URL from the API
    if (conversationId) {
      try {
        const data = await OpenHands.getVSCodeUrl(conversationId);
        if (data.vscode_url) {
          const transformedUrl = transformVSCodeUrl(data.vscode_url);
          if (transformedUrl) {
            window.open(transformedUrl, "_blank");
          }
        }
        // VS Code URL not available
      } catch (error) {
        // Failed to fetch VS Code URL
      }
    }

    setContextMenuVisible(false);
  };

  const handleDisplayCost = (event: React.MouseEvent<HTMLButtonElement>) => {
    event.stopPropagation();
    setMetricsModalVisible(true);
  };

  const handleShowAgentTools = (event: React.MouseEvent<HTMLButtonElement>) => {
    event.stopPropagation();
    setSystemModalVisible(true);
  };

  const handleShowMicroagents = (
    event: React.MouseEvent<HTMLButtonElement>,
  ) => {
    event.stopPropagation();
    setMicroagentsModalVisible(true);
  };

  React.useEffect(() => {
    if (titleMode === "edit") {
      inputRef.current?.focus();
    }
  }, [titleMode]);

  const hasContextMenu = !!(onDelete || onChangeTitle || showOptions);
  const timeBetweenUpdateAndCreation = createdAt
    ? new Date(lastUpdatedAt).getTime() - new Date(createdAt).getTime()
    : 0;
  const showUpdateTime =
    createdAt &&
    timeBetweenUpdateAndCreation > MAX_TIME_BETWEEN_CREATION_AND_UPDATE;

  return (
    <>
      <div
        data-testid="conversation-card"
        onClick={onClick}
        className={cn(
          "h-auto w-full px-[18px] py-4 border-b border-neutral-600 cursor-pointer",
          variant === "compact" &&
            "md:w-fit h-auto rounded-xl border border-[#525252]",
        )}
      >
        <div className="flex items-center justify-between w-full">
          <div className="flex items-center gap-2 flex-1 min-w-0 overflow-hidden mr-2">
            {isActive && (
              <span className="w-2 h-2 bg-blue-500 rounded-full flex-shrink-0" />
            )}
            {titleMode === "edit" && (
              <input
                ref={inputRef}
                data-testid="conversation-card-title"
                onClick={handleInputClick}
                onBlur={handleBlur}
                onKeyUp={handleKeyUp}
                type="text"
                defaultValue={title}
                className="text-sm leading-6 font-semibold bg-transparent w-full"
              />
            )}
            {titleMode === "view" && (
              <p
                data-testid="conversation-card-title"
                className="text-sm leading-6 font-semibold bg-transparent truncate overflow-hidden"
                title={title}
              >
                {title}
              </p>
            )}
          </div>

          <div className="flex items-center">
            <ConversationStateIndicator
              conversationStatus={conversationStatus}
            />
            {hasContextMenu && (
              <div className="pl-2">
                <EllipsisButton
                  onClick={(event) => {
                    event.preventDefault();
                    event.stopPropagation();
                    setContextMenuVisible((prev) => !prev);
                  }}
                />
              </div>
            )}
            <div className="relative">
              {contextMenuVisible && (
                <ConversationCardContextMenu
                  onClose={() => setContextMenuVisible(false)}
                  onDelete={onDelete && handleDelete}
                  onStop={
                    conversationStatus !== "STOPPED"
                      ? onStop && handleStop
                      : undefined
                  }
                  onEdit={onChangeTitle && handleEdit}
                  onDownloadViaVSCode={
                    conversationId && showOptions
                      ? handleDownloadViaVSCode
                      : undefined
                  }
                  onDisplayCost={showOptions ? handleDisplayCost : undefined}
                  onShowAgentTools={
                    showOptions && systemMessage
                      ? handleShowAgentTools
                      : undefined
                  }
                  onShowMicroagents={
                    showOptions && conversationId
                      ? handleShowMicroagents
                      : undefined
                  }
                  position={variant === "compact" ? "top" : "bottom"}
                />
              )}
            </div>
          </div>
        </div>

        <div
          className={cn(
            variant === "compact" && "flex flex-col justify-between mt-1",
          )}
        >
          {selectedRepository?.selected_repository && (
            <ConversationRepoLink
              selectedRepository={selectedRepository}
              variant={variant}
            />
          )}
          {(createdAt || lastUpdatedAt) && (
            <p className="text-xs text-neutral-400">
              <span>{t(I18nKey.CONVERSATION$CREATED)} </span>
              <time>
                {formatTimeDelta(new Date(createdAt || lastUpdatedAt))}{" "}
                {t(I18nKey.CONVERSATION$AGO)}
              </time>
              {showUpdateTime && (
                <>
                  <span>{t(I18nKey.CONVERSATION$UPDATED)} </span>
                  <time>
                    {formatTimeDelta(new Date(lastUpdatedAt))}{" "}
                    {t(I18nKey.CONVERSATION$AGO)}
                  </time>
                </>
              )}
            </p>
          )}
        </div>
      </div>

      <BaseModal
        isOpen={metricsModalVisible}
        onOpenChange={setMetricsModalVisible}
        title={t(I18nKey.CONVERSATION$METRICS_INFO)}
        testID="metrics-modal"
      >
        <div className="space-y-4">
          {(metrics?.cost !== null || metrics?.usage !== null) && (
            <div className="rounded-md p-3">
              <div className="grid gap-3">
                {metrics?.cost !== null && (
                  <div className="flex justify-between items-center pb-2">
                    <span className="text-lg font-semibold">
                      {t(I18nKey.CONVERSATION$TOTAL_COST)}
                    </span>
                    <span className="font-semibold">
                      ${metrics.cost.toFixed(4)}
                    </span>
                  </div>
                )}
                <BudgetDisplay
                  cost={metrics?.cost ?? null}
                  maxBudgetPerTask={metrics?.max_budget_per_task ?? null}
                />

                {metrics?.usage !== null && (
                  <>
                    <div className="flex justify-between items-center pb-2">
                      <span>{t(I18nKey.CONVERSATION$INPUT)}</span>
                      <span className="font-semibold">
                        {metrics.usage.prompt_tokens.toLocaleString()}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 gap-2 pl-4 text-sm">
                      <span className="text-neutral-400">
                        {t(I18nKey.CONVERSATION$CACHE_HIT)}
                      </span>
                      <span className="text-right">
                        {metrics.usage.cache_read_tokens.toLocaleString()}
                      </span>
                      <span className="text-neutral-400">
                        {t(I18nKey.CONVERSATION$CACHE_WRITE)}
                      </span>
                      <span className="text-right">
                        {metrics.usage.cache_write_tokens.toLocaleString()}
                      </span>
                    </div>

                    <div className="flex justify-between items-center border-b border-neutral-700 pb-2">
                      <span>{t(I18nKey.CONVERSATION$OUTPUT)}</span>
                      <span className="font-semibold">
                        {metrics.usage.completion_tokens.toLocaleString()}
                      </span>
                    </div>

                    <div className="flex justify-between items-center border-b border-neutral-700 pb-2">
                      <span className="font-semibold">
                        {t(I18nKey.CONVERSATION$TOTAL)}
                      </span>
                      <span className="font-bold">
                        {(
                          metrics.usage.prompt_tokens +
                          metrics.usage.completion_tokens
                        ).toLocaleString()}
                      </span>
                    </div>

                    <div className="flex flex-col gap-2">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold">
                          {t(I18nKey.CONVERSATION$CONTEXT_WINDOW)}
                        </span>
                      </div>
                      <div className="w-full h-1.5 bg-neutral-700 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-blue-500 transition-all duration-300"
                          style={{
                            width: `${Math.min(100, (metrics.usage.per_turn_token / metrics.usage.context_window) * 100)}%`,
                          }}
                        />
                      </div>
                      <div className="flex justify-end">
                        <span className="text-xs text-neutral-400">
                          {metrics.usage.per_turn_token.toLocaleString()} /{" "}
                          {metrics.usage.context_window.toLocaleString()} (
                          {(
                            (metrics.usage.per_turn_token /
                              metrics.usage.context_window) *
                            100
                          ).toFixed(2)}
                          % {t(I18nKey.CONVERSATION$USED)})
                        </span>
                      </div>
                    </div>
                  </>
                )}
              </div>
            </div>
          )}

          {!metrics?.cost && !metrics?.usage && (
            <div className="rounded-md p-4 text-center">
              <p className="text-neutral-400">
                {t(I18nKey.CONVERSATION$NO_METRICS)}
              </p>
            </div>
          )}
        </div>
      </BaseModal>

      <SystemMessageModal
        isOpen={systemModalVisible}
        onClose={() => setSystemModalVisible(false)}
        systemMessage={systemMessage ? systemMessage.args : null}
      />

      {microagentsModalVisible && (
        <MicroagentsModal onClose={() => setMicroagentsModalVisible(false)} />
      )}
    </>
  );
}
