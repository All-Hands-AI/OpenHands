import React, { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { SettingsDropdownInput } from "../settings/settings-dropdown-input";

export interface MicroagentInfo {
  name: string;
  trigger: string;
  description: string;
  content?: string;
}

interface MicroagentDropdownProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectMicroagent: (content: string) => void;
}

export function MicroagentDropdown({
  isOpen,
  onClose,
  onSelectMicroagent,
}: MicroagentDropdownProps) {
  const { t } = useTranslation();
  const [microagents, setMicroagents] = useState<MicroagentInfo[]>([]);
  const [selectedMicroagent, setSelectedMicroagent] =
    useState<MicroagentInfo | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);

  useEffect(() => {
    if (isOpen) {
      // Fetch microagents from the API
      fetch("/api/options/microagents")
        .then((response) => response.json())
        .then((data: MicroagentInfo[]) => {
          setMicroagents(data);
        })
        .catch(() => {
          // Error handling for microagents fetch
        });
    } else {
      setSelectedMicroagent(null);
      setIsExpanded(false);
    }
  }, [isOpen]);

  if (!isOpen) {
    return null;
  }

  const handleSelectionChange = (key: React.Key | null) => {
    if (key === null) {
      setSelectedMicroagent(null);
      return;
    }

    const selected = microagents.find((m) => m.name === key);
    if (selected) {
      setSelectedMicroagent(selected);

      // If the microagent has content, we can use it directly
      if (selected.content) {
        onSelectMicroagent(selected.content);
        onClose();
      } else {
        // Otherwise, we need to fetch the content
        fetch(`/api/options/microagents/${selected.name}`)
          .then((response) => response.json())
          .then((data) => {
            if (data.content) {
              onSelectMicroagent(data.content);
              onClose();
            }
          })
          .catch(() => {
            // Error handling for specific microagent fetch
          });
      }
    }
  };

  const toggleExpand = () => {
    setIsExpanded(!isExpanded);
  };

  const dropdownItems = microagents.map((microagent) => ({
    key: microagent.name,
    label: microagent.name,
  }));

  return (
    <div className="absolute bottom-full mb-2 w-full bg-tertiary rounded-xl border border-[#717888] p-4 z-10">
      <div className="flex flex-col gap-4">
        <h3 className="text-lg font-medium">
          {t(I18nKey.BUTTON$SELECT_MICROAGENT)}
        </h3>
        <SettingsDropdownInput
          testId="microagent-dropdown"
          name="microagent-dropdown"
          placeholder={t(I18nKey.BUTTON$SELECT_MICROAGENT)}
          items={dropdownItems}
          onSelectionChange={handleSelectionChange}
          wrapperClassName="w-full"
        />

        {selectedMicroagent && (
          <div className="mt-2">
            <div className="flex justify-between items-center">
              <h4 className="text-md font-medium">{selectedMicroagent.name}</h4>
              <span className="text-sm text-gray-400">
                {selectedMicroagent.trigger}
              </span>
            </div>
            <p className="text-sm mt-1">{selectedMicroagent.description}</p>

            {selectedMicroagent.content && (
              <div className="mt-2">
                <div className="bg-gray-800 p-2 rounded text-sm font-mono">
                  {isExpanded
                    ? selectedMicroagent.content
                    : selectedMicroagent.content
                        .split("\n")
                        .slice(0, 5)
                        .join("\n")}
                </div>
                {selectedMicroagent.content.split("\n").length > 5 && (
                  <button
                    type="button"
                    onClick={toggleExpand}
                    className="text-sm text-blue-400 mt-1"
                  >
                    {isExpanded
                      ? t(I18nKey.BUTTON$SHOW_LESS)
                      : t(I18nKey.BUTTON$SHOW_MORE)}
                  </button>
                )}
              </div>
            )}
          </div>
        )}

        <div className="flex justify-end">
          <button
            type="button"
            onClick={onClose}
            className="px-3 py-1 bg-gray-700 rounded text-sm"
          >
            {t(I18nKey.BUTTON$CANCEL)}
          </button>
        </div>
      </div>
    </div>
  );
}
