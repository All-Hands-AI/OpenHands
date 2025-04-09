import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { SettingsDropdownInput } from "../settings-dropdown-input";

interface AgentInputProps {
  agents: string[];
  defaultAgent: string;
}

export function AgentInput({ agents, defaultAgent }: AgentInputProps) {
  const { t } = useTranslation();

  return (
    <SettingsDropdownInput
      testId="agent-input"
      name="agent-input"
      label={t(I18nKey.SETTINGS$AGENT)}
      items={
        agents.map((agent) => ({
          key: agent,
          label: agent,
        })) || []
      }
      defaultSelectedKey={defaultAgent}
      isClearable={false}
    />
  );
}
