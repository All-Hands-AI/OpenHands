import { useState } from "react";
import { useTranslation } from "react-i18next";
import { ModalBackdrop } from "#/components/shared/modals/modal-backdrop";
import { ModalBody } from "#/components/shared/modals/modal-body";
import { I18nKey } from "#/i18n/declaration";
import { useConversationMicroagents } from "#/hooks/query/use-conversation-microagents";
import { AgentState } from "#/types/agent-state";
import { Typography } from "#/ui/typography";
import { MicroagentsModalHeader } from "./microagents-modal-header";
import { MicroagentsLoadingState } from "./microagents-loading-state";
import { MicroagentsEmptyState } from "./microagents-empty-state";
import { MicroagentItem } from "./microagent-item";
import { useAgentStore } from "#/stores/agent-store";

interface MicroagentsModalProps {
  onClose: () => void;
}

export function MicroagentsModal({ onClose }: MicroagentsModalProps) {
  const { t } = useTranslation();
  const { curAgentState } = useAgentStore();
  const [expandedAgents, setExpandedAgents] = useState<Record<string, boolean>>(
    {},
  );
  const {
    data: microagents,
    isLoading,
    isError,
    refetch,
    isRefetching,
  } = useConversationMicroagents();

  const toggleAgent = (agentName: string) => {
    setExpandedAgents((prev) => ({
      ...prev,
      [agentName]: !prev[agentName],
    }));
  };

  const isAgentReady = ![AgentState.LOADING, AgentState.INIT].includes(
    curAgentState,
  );

  return (
    <ModalBackdrop onClose={onClose}>
      <ModalBody
        width="medium"
        className="max-h-[80vh] flex flex-col items-start"
        testID="microagents-modal"
      >
        <MicroagentsModalHeader
          isAgentReady={isAgentReady}
          isLoading={isLoading}
          isRefetching={isRefetching}
          onRefresh={refetch}
        />

        {isAgentReady && (
          <Typography.Text className="text-sm text-gray-400">
            {t(I18nKey.MICROAGENTS_MODAL$WARNING)}
          </Typography.Text>
        )}

        <div className="w-full h-[60vh] overflow-auto rounded-md custom-scrollbar-always">
          {!isAgentReady && (
            <div className="w-full h-full flex items-center text-center justify-center text-2xl text-tertiary-light">
              <Typography.Text>
                {t(I18nKey.DIFF_VIEWER$WAITING_FOR_RUNTIME)}
              </Typography.Text>
            </div>
          )}

          {isLoading && <MicroagentsLoadingState />}

          {!isLoading &&
            isAgentReady &&
            (isError || !microagents || microagents.length === 0) && (
              <MicroagentsEmptyState isError={isError} />
            )}

          {!isLoading &&
            isAgentReady &&
            microagents &&
            microagents.length > 0 && (
              <div className="p-2 space-y-3">
                {microagents.map((agent) => {
                  const isExpanded = expandedAgents[agent.name] || false;

                  return (
                    <MicroagentItem
                      key={agent.name}
                      agent={agent}
                      isExpanded={isExpanded}
                      onToggle={toggleAgent}
                    />
                  );
                })}
              </div>
            )}
        </div>
      </ModalBody>
    </ModalBackdrop>
  );
}
