import { useTranslation } from "react-i18next";
import { constructRepositoryUrl } from "#/utils/utils";
import { Provider } from "#/types/settings";
import { I18nKey } from "#/i18n/declaration";
import { GitProviderIcon } from "#/components/shared/git-provider-icon";
import RepoForkedIcon from "#/icons/repo-forked.svg?react";
import { GitControlButton } from "./git-control-button";

interface GitControlBarRepoButtonProps {
  selectedRepository: string | null | undefined;
  gitProvider: Provider | null | undefined;
}

export function GitControlBarRepoButton({
  selectedRepository,
  gitProvider,
}: GitControlBarRepoButtonProps) {
  const { t } = useTranslation();

  const hasRepository = selectedRepository && gitProvider;

  const repositoryUrl = hasRepository
    ? constructRepositoryUrl(gitProvider, selectedRepository)
    : undefined;

  return (
    <GitControlButton
      as="a"
      href={hasRepository ? repositoryUrl : undefined}
      target="_blank"
      rel="noopener noreferrer"
      size="wide"
      width="extra-large"
      enabled={!!hasRepository}
      showExternalLink={!!hasRepository}
      icon={
        hasRepository ? (
          <GitProviderIcon
            gitProvider={gitProvider as Provider}
            className="w-3 h-3 inline-flex"
          />
        ) : (
          <RepoForkedIcon width={12} height={12} color="white" />
        )
      }
      text={
        hasRepository ? selectedRepository : t(I18nKey.COMMON$NO_REPO_CONNECTED)
      }
    />
  );
}
