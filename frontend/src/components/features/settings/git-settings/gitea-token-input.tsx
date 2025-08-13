import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { SettingsInput } from "../settings-input";
import { GiteaTokenHelpAnchor } from "./gitea-token-help-anchor";
import { KeyStatusIcon } from "../key-status-icon";
import { cn } from "#/utils/utils";

interface GiteaTokenInputProps {
  onChange: (value: string) => void;
  onGiteaHostChange: (value: string) => void;
  isGiteaTokenSet: boolean;
  name: string;
  giteaHostSet: string | null | undefined;
  className?: string;
}

export function GiteaTokenInput({
  onChange,
  onGiteaHostChange,
  isGiteaTokenSet,
  name,
  giteaHostSet,
  className,
}: GiteaTokenInputProps) {
  const { t } = useTranslation();

  return (
    <div className={cn("flex flex-col gap-6", className)}>
      <SettingsInput
        testId={name}
        name={name}
        onChange={onChange}
        label={t(I18nKey.GITEA$TOKEN_LABEL)}
        type="password"
        className="w-full max-w-[680px]"
        placeholder={isGiteaTokenSet ? "<hidden>" : ""}
        startContent={
          isGiteaTokenSet && (
            <KeyStatusIcon
              testId="gitea-set-token-indicator"
              isSet={isGiteaTokenSet}
            />
          )
        }
      />

      <SettingsInput
        onChange={onGiteaHostChange || (() => {})}
        name="gitea-host-input"
        testId="gitea-host-input"
        label={t(I18nKey.GITEA$HOST_LABEL)}
        type="text"
        className="w-full max-w-[680px]"
        placeholder="gitea.com"
        defaultValue={giteaHostSet || undefined}
        startContent={
          giteaHostSet &&
          giteaHostSet.trim() !== "" && (
            <KeyStatusIcon testId="gitea-set-host-indicator" isSet />
          )
        }
      />

      <GiteaTokenHelpAnchor />
    </div>
  );
}
