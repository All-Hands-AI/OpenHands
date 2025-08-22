import { useTranslation } from "react-i18next";
import BranchIcon from "#/icons/u-code-branch.svg?react";
import LinkExternalIcon from "#/icons/link-external.svg?react";
import { constructBranchUrl, cn } from "#/utils/utils";
import { Provider } from "#/types/settings";
import { I18nKey } from "#/i18n/declaration";

interface GitControlBarBranchButtonProps {
  selectedBranch: string | null | undefined;
  selectedRepository: string | null | undefined;
  gitProvider: Provider | null | undefined;
}

export function GitControlBarBranchButton({
  selectedBranch,
  selectedRepository,
  gitProvider,
}: GitControlBarBranchButtonProps) {
  const { t } = useTranslation();

  const hasBranch = selectedBranch && selectedRepository && gitProvider;
  const branchUrl = hasBranch
    ? constructBranchUrl(gitProvider, selectedRepository, selectedBranch)
    : undefined;

  return (
    <a
      href={hasBranch ? branchUrl : undefined}
      target="_blank"
      rel="noopener noreferrer"
      className={cn(
        "group flex items-center justify-between gap-2 pl-2.5 pr-2.5 py-1 rounded-[100px]",
        hasBranch
          ? "bg-[#25272D] hover:bg-[#525662] cursor-pointer"
          : "bg-[rgba(71,74,84,0.50)] cursor-not-allowed",
      )}
    >
      <div className="flex flex-row gap-2 items-center justify-start">
        <div className="w-3 h-3 flex items-center justify-center">
          <BranchIcon width={12} height={12} color="white" />
        </div>
        <div className="font-normal text-white text-sm leading-5">
          {hasBranch ? selectedBranch : t(I18nKey.COMMON$NO_BRANCH)}
        </div>
      </div>

      {hasBranch && (
        <div className="w-3 h-3 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
          <LinkExternalIcon width={12} height={12} color="white" />
        </div>
      )}
    </a>
  );
}
