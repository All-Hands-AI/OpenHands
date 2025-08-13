import { useTranslation } from "react-i18next";
import LinkExternalIcon from "#/icons/link-external.svg?react";
import { constructRepositoryUrl, cn } from "#/utils/utils";
import { Provider } from "#/types/settings";
import { I18nKey } from "#/i18n/declaration";
import { GitProviderIcon } from "#/components/shared/git-provider-icon";
import RepoForkedIcon from "#/icons/repo-forked.svg?react";

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
    <a
      href={hasRepository ? repositoryUrl : undefined}
      target="_blank"
      rel="noopener noreferrer"
      className={cn(
        "group flex flex-row items-center justify-between pl-2.5 pr-2.5 py-1 rounded-[100px]",
        hasRepository
          ? "bg-[#25272D] hover:bg-[#525662] cursor-pointer"
          : "bg-[rgba(71,74,84,0.50)] cursor-not-allowed",
      )}
    >
      <div className="flex flex-row gap-2 items-center justify-start">
        <div className="w-3 h-3 flex items-center justify-center">
          {hasRepository ? (
            <GitProviderIcon
              gitProvider={gitProvider as Provider}
              className="w-3 h-3 inline-flex"
            />
          ) : (
            <RepoForkedIcon width={12} height={12} color="white" />
          )}
        </div>
        <div className="font-normal text-white text-sm leading-5">
          {hasRepository
            ? selectedRepository
            : t(I18nKey.COMMON$NO_REPO_CONNECTED)}
        </div>
      </div>
      {hasRepository && (
        <div className="w-3 h-3 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
          <LinkExternalIcon width={12} height={12} color="white" />
        </div>
      )}
    </a>
  );
}
