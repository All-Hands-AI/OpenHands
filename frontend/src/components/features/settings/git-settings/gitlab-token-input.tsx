import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { SettingsInput } from "../settings-input";
import { GitLabTokenHelpAnchor } from "./gitlab-token-help-anchor";
import { KeyStatusIcon } from "../key-status-icon";

interface GitLabTokenInputProps {
  onChange: (value: string) => void;
  onGitLabHostChange: (value: string) => void;
  isGitLabTokenSet: boolean;
  name: string;
  gitlabHostSet: string | null | undefined;
}

export function GitLabTokenInput({
  onChange,
  onGitLabHostChange,
  isGitLabTokenSet,
  name,
  gitlabHostSet,
}: GitLabTokenInputProps) {
  const { t } = useTranslation();

  return (
    <div className="flex flex-col gap-6">
      <SettingsInput
        testId={name}
        name={name}
        onChange={onChange}
        label={t(I18nKey.GITLAB$TOKEN_LABEL)}
        type="password"
        className="w-full max-w-[680px]"
        placeholder={isGitLabTokenSet ? "<hidden>" : ""}
        startContent={
          isGitLabTokenSet && (
            <KeyStatusIcon
              testId="gl-set-token-indicator"
              isSet={isGitLabTokenSet}
            />
          )
        }
      />

      <SettingsInput
        onChange={onGitLabHostChange || (() => {})}
        name="gitlab-host-input"
        testId="gitlab-host-input"
        label={t(I18nKey.GITLAB$HOST_LABEL)}
        type="text"
        className="w-full max-w-[680px]"
        placeholder="gitlab.com"
        defaultValue={gitlabHostSet || undefined}
        startContent={
          gitlabHostSet &&
          gitlabHostSet.trim() !== "" && (
            <KeyStatusIcon testId="gl-set-host-indicator" isSet />
          )
        }
      />

      <GitLabTokenHelpAnchor />
    </div>
  );
}
