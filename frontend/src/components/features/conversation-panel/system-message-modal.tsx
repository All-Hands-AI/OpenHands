import React from "react";
import { useTranslation } from "react-i18next";
import { BaseModalTitle } from "#/components/shared/modals/confirmation-modals/base-modal";
import { ModalBackdrop } from "#/components/shared/modals/modal-backdrop";
import { ModalBody } from "#/components/shared/modals/modal-body";
import { BrandButton } from "../settings/brand-button";
import { I18nKey } from "#/i18n/declaration";

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

  if (!systemMessage) {
    return null;
  }

  return (
    isOpen && (
      <ModalBackdrop onClose={onClose}>
        <ModalBody className="max-w-4xl max-h-[80vh] flex flex-col items-start">
          <div className="flex flex-col gap-2 w-full">
            <BaseModalTitle title="Agent Tools & Metadata" />
            <div className="flex flex-col gap-1">
              {systemMessage.agent_class && (
                <div className="text-sm">
                  <strong>Agent Class:</strong> {systemMessage.agent_class}
                </div>
              )}
              {systemMessage.openhands_version && (
                <div className="text-sm">
                  <strong>OpenHands Version:</strong>{" "}
                  {systemMessage.openhands_version}
                </div>
              )}
            </div>
          </div>

          <div className="w-full mt-4">
            <div className="flex border-b mb-4">
              <button
                type="button"
                className="px-4 py-2 font-medium border-b-2 border-primary"
                onClick={() => {}}
              >
                System Message
              </button>
            </div>

            <div className="max-h-[50vh] overflow-auto">
              <div className="p-4 whitespace-pre-wrap font-mono text-sm">
                {systemMessage.content}
              </div>
            </div>

            {systemMessage.tools && systemMessage.tools.length > 0 && (
              <div className="mt-6">
                <h3 className="font-medium mb-2">Available Tools:</h3>
                <div className="space-y-4">
                  {systemMessage.tools.map((tool, index) => (
                    <div key={index} className="border rounded-md p-4">
                      <h3 className="font-bold">{String(tool.name || "")}</h3>
                      <p className="text-sm whitespace-pre-wrap">
                        {String(tool.description || "")}
                      </p>
                      {tool.parameters ? (
                        <div className="mt-2">
                          <h4 className="text-sm font-semibold">Parameters:</h4>
                          <pre className="text-xs mt-1 p-2 bg-gray-100 dark:bg-gray-800 rounded-md overflow-auto">
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

          <div className="w-full mt-4">
            <BrandButton
              type="button"
              variant="secondary"
              onClick={onClose}
              className="w-full"
            >
              {t(I18nKey.BUTTON$CLOSE)}
            </BrandButton>
          </div>
        </ModalBody>
      </ModalBackdrop>
    )
  );
}
