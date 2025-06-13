import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { SettingsInput } from "../settings-input";
import { BitbucketTokenHelpAnchor } from "./bitbucket-token-help-anchor";
import { KeyStatusIcon } from "../key-status-icon";

interface BitbucketTokenInputProps {
  onChange: (value: string) => void;
  onBitbucketHostChange: (value: string) => void;
  isBitbucketTokenSet: boolean;
  name: string;
  bitbucketHostSet: string | null | undefined;
}

export function BitbucketTokenInput({
  onChange,
  onBitbucketHostChange,
  isBitbucketTokenSet,
  name,
  bitbucketHostSet,
}: BitbucketTokenInputProps) {
  const { t } = useTranslation();

  return (
    <div className="flex flex-col gap-6">
      <SettingsInput
        testId={name}
        name={name}
        onChange={onChange}
        label={t(I18nKey.BITBUCKET$TOKEN_LABEL)}
        type="password"
        className="w-full max-w-[680px]"
        placeholder={isBitbucketTokenSet ? "<hidden>" : "username:app_password"}
        startContent={
          isBitbucketTokenSet && (
            <KeyStatusIcon
              testId="bb-set-token-indicator"
              isSet={isBitbucketTokenSet}
            />
          )
        }
      />

      <SettingsInput
        onChange={onBitbucketHostChange || (() => {})}
        name="bitbucket-host-input"
        testId="bitbucket-host-input"
        label={t(I18nKey.BITBUCKET$HOST_LABEL)}
        type="text"
        className="w-full max-w-[680px]"
        placeholder="bitbucket.org"
        defaultValue={bitbucketHostSet || undefined}
        startContent={
          bitbucketHostSet &&
          bitbucketHostSet.trim() !== "" && (
            <KeyStatusIcon testId="bb-set-host-indicator" isSet />
          )
        }
      />

      <BitbucketTokenHelpAnchor />
    </div>
  );
}
