import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { SettingsInput } from "../settings-input";
import { BitbucketTokenHelpAnchor } from "./bitbucket-token-help-anchor";
import { KeyStatusIcon } from "../key-status-icon";
import { cn } from "#/utils/utils";
import type { BitbucketMode } from "#/types/settings";

interface BitbucketTokenInputProps {
  onChange: (value: string) => void;
  onBitbucketHostChange: (value: string) => void;
  onBitbucketModeChange: (value: BitbucketMode) => void;
  isBitbucketTokenSet: boolean;
  name: string;
  bitbucketHostSet: string | null | undefined;
  bitbucketMode: BitbucketMode;
  className?: string;
}

export function BitbucketTokenInput({
  onChange,
  onBitbucketHostChange,
  onBitbucketModeChange,
  isBitbucketTokenSet,
  name,
  bitbucketHostSet,
  bitbucketMode,
  className,
}: BitbucketTokenInputProps) {
  const { t } = useTranslation();

  return (
    <div className={cn("flex flex-col gap-6", className)}>
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

      <div className="flex flex-col gap-2.5 w-fit">
        <label
          className="flex items-center gap-2 text-sm"
          htmlFor="bitbucket-mode-input"
        >
          {t(I18nKey.BITBUCKET$MODE_LABEL)}
        </label>
        <select
          data-testid="bitbucket-mode-input"
          name="bitbucket-mode-input"
          id="bitbucket-mode-input"
          value={bitbucketMode}
          onChange={(event) =>
            onBitbucketModeChange(event.target.value as BitbucketMode)
          }
          className={cn(
            "bg-tertiary border border-[#717888] h-10 w-full max-w-[680px] rounded-sm p-2",
            "text-white",
          )}
        >
          <option value="cloud">
            {t(I18nKey.BITBUCKET$MODE_OPTION_CLOUD)}
          </option>
          <option value="server">
            {t(I18nKey.BITBUCKET$MODE_OPTION_SERVER)}
          </option>
        </select>
      </div>

      <BitbucketTokenHelpAnchor />
    </div>
  );
}
