import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { SettingsInput } from "../settings-input";
import { AzureDevOpsTokenHelpAnchor } from "./azure-devops-token-help-anchor";
import { KeyStatusIcon } from "../key-status-icon";

interface AzureDevOpsTokenInputProps {
  onChange: (value: string) => void;
  onAzureDevOpsHostChange: (value: string) => void;
  isAzureDevOpsTokenSet: boolean;
  name: string;
  azureDevOpsHostSet: string | null | undefined;
}

export function AzureDevOpsTokenInput({
  onChange,
  onAzureDevOpsHostChange,
  isAzureDevOpsTokenSet,
  name,
  azureDevOpsHostSet,
}: AzureDevOpsTokenInputProps) {
  const { t } = useTranslation();

  return (
    <div className="flex flex-col gap-6">
      <SettingsInput
        testId={name}
        name={name}
        onChange={onChange}
        label={t(I18nKey.AZURE_DEVOPS$TOKEN_LABEL)}
        type="password"
        className="w-[680px]"
        placeholder={isAzureDevOpsTokenSet ? "<hidden>" : ""}
        startContent={
          isAzureDevOpsTokenSet && (
            <KeyStatusIcon
              testId="ado-set-token-indicator"
              isSet={isAzureDevOpsTokenSet}
            />
          )
        }
      />

      <SettingsInput
        onChange={onAzureDevOpsHostChange || (() => {})}
        name="azure-devops-host-input"
        testId="azure-devops-host-input"
        label={t(I18nKey.AZURE_DEVOPS$HOST_LABEL)}
        type="text"
        className="w-[680px]"
        placeholder="dev.azure.com"
        defaultValue={azureDevOpsHostSet || undefined}
        startContent={
          azureDevOpsHostSet &&
          azureDevOpsHostSet.trim() !== "" && (
            <KeyStatusIcon testId="ado-set-host-indicator" isSet />
          )
        }
      />

      <AzureDevOpsTokenHelpAnchor />
    </div>
  );
}
