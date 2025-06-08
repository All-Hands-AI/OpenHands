import React from "react";
import { useTranslation } from "react-i18next";
import { BaseModal } from "../../shared/modals/base-modal/base-modal";
import { Microagent } from "#/api/open-hands.types";
import { I18nKey } from "#/i18n/declaration";

interface MicroagentsModalProps {
  isOpen: boolean;
  onClose: () => void;
  microagents: Microagent[] | null;
  isLoading: boolean;
}

export function MicroagentsModal({
  isOpen,
  onClose,
  microagents,
  isLoading,
}: MicroagentsModalProps) {
  const { t } = useTranslation();
  return (
    <BaseModal
      isOpen={isOpen}
      onOpenChange={onClose}
      title="Microagents"
      testID="microagents-modal"
    >
      <div className="space-y-4">
        {isLoading && (
          <div className="flex justify-center items-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500" />
          </div>
        )}

        {!isLoading && (!microagents || microagents.length === 0) && (
          <div className="rounded-md p-4 text-center">
            <p className="text-neutral-400">
              {t(I18nKey.CONVERSATION$NO_MICROAGENTS)}
            </p>
          </div>
        )}

        {!isLoading && microagents && microagents.length > 0 && (
          <div className="space-y-4 max-h-[600px] overflow-y-auto pr-1">
            {microagents.map((agent) => (
              <div
                key={agent.name}
                className="border border-neutral-700 rounded-md p-4 max-h-[400px] overflow-y-auto"
              >
                <div className="flex justify-between items-center mb-2">
                  <h3 className="text-lg font-semibold">{agent.name}</h3>
                  <span className="px-2 py-1 text-xs rounded-full bg-neutral-800">
                    {agent.type === "repo" ? "Repository" : "Knowledge"}
                  </span>
                </div>

                {agent.triggers && agent.triggers.length > 0 && (
                  <div className="mb-2">
                    <p className="text-sm text-neutral-400 mb-1">Triggers:</p>
                    <div className="flex flex-wrap gap-1">
                      {agent.triggers.map((trigger) => (
                        <span
                          key={trigger}
                          className="px-2 py-1 text-xs rounded-full bg-blue-900"
                        >
                          {trigger}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                <div className="mt-2">
                  <p className="text-sm text-neutral-400 mb-1">Content:</p>
                  <pre className="bg-neutral-900 p-2 rounded-md text-xs overflow-auto max-h-60">
                    {agent.content}
                  </pre>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </BaseModal>
  );
}
