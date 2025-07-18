import React from "react";
import { SettingsDropdownInput } from "../settings-dropdown-input";

interface SystemPromptSelectorProps {
  name: string;
  defaultValue?: string;
  onChange?: (value: string) => void;
}

const SYSTEM_PROMPT_OPTIONS = [
  {
    key: "system_prompt.j2",
    label: "Default",
  },
  {
    key: "system_prompt_interactive.j2",
    label: "Interactive (Experimental)",
  },
  {
    key: "system_prompt_todo_list.j2",
    label: "TODO List (Experimental)",
  },
];

export function SystemPromptSelector({
  name,
  defaultValue = "system_prompt.j2",
  onChange,
}: SystemPromptSelectorProps) {
  const handleSelectionChange = (key: React.Key | null) => {
    if (key && onChange) {
      onChange(key.toString());
    }
  };

  return (
    <SettingsDropdownInput
      testId="system-prompt-selector"
      name={name}
      label={
        <div className="flex items-center gap-2">
          {/* eslint-disable-next-line i18next/no-literal-string */}
          <span>System Prompt</span>
          {/* eslint-disable-next-line i18next/no-literal-string */}
          <span className="text-xs bg-orange-500/20 text-orange-400 px-2 py-1 rounded-full">
            Experimental
          </span>
        </div>
      }
      items={SYSTEM_PROMPT_OPTIONS}
      defaultSelectedKey={defaultValue}
      onSelectionChange={handleSelectionChange}
      placeholder="Select system prompt variant"
      wrapperClassName="w-full max-w-[680px]"
    />
  );
}
