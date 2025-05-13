import React from "react";
import { SettingsDropdownInput } from "../../settings/settings-dropdown-input";

export interface BranchDropdownProps {
  items: { key: React.Key; label: string }[];
  onSelectionChange: (key: React.Key | null) => void;
  isDisabled: boolean;
  selectedKey?: string;
}

export function BranchDropdown({
  items,
  onSelectionChange,
  isDisabled,
  selectedKey,
}: BranchDropdownProps) {
  return (
    <SettingsDropdownInput
      testId="branch-dropdown"
      name="branch-dropdown"
      placeholder="Select a branch"
      items={items}
      wrapperClassName="max-w-[500px]"
      onSelectionChange={onSelectionChange}
      isDisabled={isDisabled}
      selectedKey={selectedKey}
    />
  );
}
