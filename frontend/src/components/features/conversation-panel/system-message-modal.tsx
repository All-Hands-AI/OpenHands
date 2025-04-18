import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { BaseModalTitle } from "#/components/shared/modals/confirmation-modals/base-modal";
import { ModalBackdrop } from "#/components/shared/modals/modal-backdrop";
import { ModalBody } from "#/components/shared/modals/modal-body";
import { BrandButton } from "../settings/brand-button";
import { I18nKey } from "#/i18n/declaration";
import { cn } from "#/utils/utils";

interface SystemMessageModalProps {
  isOpen: boolean;
  onClose: () => void;
  systemMessage: {
    content: string;
    tools: Array<Record<string, unknown>> | null;
    openhands_version: string | null;
    agent_class: string | null;
  } | null;
}

export function SystemMessageModal({
  isOpen,
  onClose,
  systemMessage,
}: SystemMessageModalProps) {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<"system" | "tools">("system");

  if (!systemMessage) {
    return null;
  }

  return (
    isOpen && (
      <ModalBackdrop onClose={onClose}>
        <ModalBody className="max-w-4xl max-h-[80vh] flex flex-col items-start">
          <div className="flex flex-col gap-2 w-full">
            <BaseModalTitle title="Agent Tools & Metadata" />
            <div className="flex flex-col gap-2 p-3 bg-gray-50 dark:bg-gray-800 rounded-md mb-4">
              {systemMessage.agent_class && (
                <div className="text-sm">
                  <span className="font-semibold text-gray-700 dark:text-gray-300">Agent Class:</span>{" "}
                  <span className="font-medium text-primary">{systemMessage.agent_class}</span>
                </div>
              )}
              {systemMessage.openhands_version && (
                <div className="text-sm">
                  <span className="font-semibold text-gray-700 dark:text-gray-300">OpenHands Version:</span>{" "}
                  <span>{systemMessage.openhands_version}</span>
                </div>
              )}
            </div>
          </div>

          <div className="w-full">
            <div className="flex border-b mb-4">
              <button
                type="button"
                className={cn(
                  "px-4 py-2 font-medium border-b-2 transition-colors",
                  activeTab === "system" 
                    ? "border-primary text-primary" 
                    : "border-transparent hover:text-gray-700 dark:hover:text-gray-300"
                )}
                onClick={() => setActiveTab("system")}
              >
                System Message
              </button>
              {systemMessage.tools && systemMessage.tools.length > 0 && (
                <button
                  type="button"
                  className={cn(
                    "px-4 py-2 font-medium border-b-2 transition-colors",
                    activeTab === "tools" 
                      ? "border-primary text-primary" 
                      : "border-transparent hover:text-gray-700 dark:hover:text-gray-300"
                  )}
                  onClick={() => setActiveTab("tools")}
                >
                  Available Tools
                </button>
              )}
            </div>

            {activeTab === "system" && (
              <div className="max-h-[50vh] overflow-auto rounded-md border border-gray-200 dark:border-gray-700">
                <div className="p-4 whitespace-pre-wrap font-mono text-sm">
                  {systemMessage.content}
                </div>
              </div>
            )}

            {activeTab === "tools" && systemMessage.tools && systemMessage.tools.length > 0 && (
              <div className="max-h-[50vh] overflow-auto">
                <div className="space-y-4">
                  {systemMessage.tools.map((tool, index) => (
                    <div key={index} className="border rounded-md p-4 bg-gray-50 dark:bg-gray-800">
                      <h3 className="font-bold text-primary">{String(tool.name || "")}</h3>
                      <p className="text-sm whitespace-pre-wrap mt-1">
                        {String(tool.description || "")}
                      </p>
                      {tool.parameters ? (
                        <div className="mt-3">
                          <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300">Parameters:</h4>
                          <pre className="text-xs mt-1 p-3 bg-gray-100 dark:bg-gray-900 rounded-md overflow-auto border border-gray-200 dark:border-gray-700">
                            {JSON.stringify(tool.parameters, null, 2)}
                          </pre>
                        </div>
                      ) : null}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="w-full mt-6 flex justify-end">
            <BrandButton
              type="button"
              variant="secondary"
              onClick={onClose}
              className="px-6"
            >
              {t(I18nKey.BUTTON$CLOSE)}
            </BrandButton>
          </div>
        </ModalBody>
      </ModalBackdrop>
    )
  );
}
