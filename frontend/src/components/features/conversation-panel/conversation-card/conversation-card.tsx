import React from "react";
import { useSelector } from "react-redux";
import posthog from "posthog-js";
import { useTranslation } from "react-i18next";
import { formatTimeDelta } from "#/utils/format-time-delta";
import { ConversationRepoLink } from "./conversation-repo-link";
import { ConversationCardContextMenu } from "./conversation-card-context-menu";
import { SystemMessageModal } from "../system-message-modal";
import { MicroagentsModal } from "../microagents-modal";
import { BudgetDisplay } from "../budget-display";
import { cn } from "#/utils/utils";
import { BaseModal } from "../../../shared/modals/base-modal/base-modal";
import { RootState } from "#/store";
import { I18nKey } from "#/i18n/declaration";
import { transformVSCodeUrl } from "#/utils/vscode-url-helper";
import OpenHands from "#/api/open-hands";
import { useWsClient } from "#/context/ws-client-provider";
import { isSystemMessage } from "#/types/core/guards";
import { ConversationStatus } from "#/types/conversation-status";
import { RepositorySelection } from "#/api/open-hands.types";
import EllipsisIcon from "#/icons/ellipsis.svg?react";
import { ConversationCardTitle } from "./conversation-card-title";

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
  conversationId?: string; // Optional conversation ID for VS Code URL
  contextMenuOpen?: boolean;
  onContextMenuToggle?: (isOpen: boolean) => void;
}

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
  conversationId,
  conversationStatus,
  contextMenuOpen = false,
  onContextMenuToggle,
}: ConversationCardProps) {
  const { t } = useTranslation();
  const { parsedEvents } = useWsClient();
  const [titleMode, setTitleMode] = React.useState<"view" | "edit">("view");
  const [metricsModalVisible, setMetricsModalVisible] = React.useState(false);
  const [systemModalVisible, setSystemModalVisible] = React.useState(false);
  const [microagentsModalVisible, setMicroagentsModalVisible] =
    React.useState(false);

  const systemMessage = parsedEvents.find(isSystemMessage);

  // Subscribe to metrics data from Redux store
  const metrics = useSelector((state: RootState) => state.metrics);

  const onTitleSave = (newTitle: string) => {
    if (newTitle !== "" && newTitle !== title) {
      onChangeTitle?.(newTitle);
    }
    setTitleMode("view");
  };

  const handleDelete = (event: React.MouseEvent<HTMLButtonElement>) => {
    event.preventDefault();
    event.stopPropagation();
    onDelete?.();
    onContextMenuToggle?.(false);
  };

  const handleStop = (event: React.MouseEvent<HTMLButtonElement>) => {
    event.preventDefault();
    event.stopPropagation();
    onStop?.();
    onContextMenuToggle?.(false);
  };

  const handleEdit = (event: React.MouseEvent<HTMLButtonElement>) => {
    event.preventDefault();
    event.stopPropagation();
    setTitleMode("edit");
    onContextMenuToggle?.(false);
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

    onContextMenuToggle?.(false);
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

  const hasContextMenu = !!(onDelete || onChangeTitle || showOptions);

  return (
    <>
      <div
        data-testid="conversation-card"
        data-context-menu-open={contextMenuOpen.toString()}
        onClick={onClick}
        className={cn(
          "relative h-auto w-full p-3.5 border-b border-neutral-600 cursor-pointer",
          "data-[context-menu-open=false]:hover:bg-[#454545]",
        )}
      >
        <div className="flex items-center justify-between w-full">
          <div className="flex items-center gap-2 flex-1 min-w-0 overflow-hidden mr-2">
            {isActive && (
              <span className="w-2 h-2 bg-[#1FBD53] rounded-full flex-shrink-0" />
            )}
            <ConversationCardTitle
              title={title}
              titleMode={titleMode}
              onSave={onTitleSave}
            />
          </div>

          {hasContextMenu && (
            <div className="absolute top-0 right-0">
              <button
                data-testid="ellipsis-button"
                type="button"
                onClick={(event) => {
                  event.preventDefault();
                  event.stopPropagation();
                  onContextMenuToggle?.(!contextMenuOpen);
                }}
                className="cursor-pointer w-6 h-6 pt-2.25 pr-1 flex flex-row items-center justify-center"
              >
                <EllipsisIcon />
              </button>
              <div className="relative">
                {contextMenuOpen && (
                  <ConversationCardContextMenu
                    onClose={() => onContextMenuToggle?.(false)}
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
                    position="bottom"
                  />
                )}
              </div>
            </div>
          )}
        </div>

        <div className={cn("flex flex-row justify-between items-center mt-1")}>
          {selectedRepository?.selected_repository && (
            <ConversationRepoLink selectedRepository={selectedRepository} />
          )}
          {(createdAt ?? lastUpdatedAt) && (
            <p className="text-xs text-[#A3A3A3] flex-1 text-right">
              <time>
                {`${formatTimeDelta(new Date(lastUpdatedAt ?? createdAt))} ${t(I18nKey.CONVERSATION$AGO)}`}
              </time>
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
