import { useTranslation } from "react-i18next";
import BranchIcon from "#/icons/u-code-branch.svg?react";
import { constructBranchUrl } from "#/utils/utils";
import { Provider } from "#/types/settings";
import { I18nKey } from "#/i18n/declaration";
import { GitControlButton } from "./git-control-button";

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
    <GitControlButton
      as="a"
      href={hasBranch ? branchUrl : undefined}
      target="_blank"
      rel="noopener noreferrer"
      size="wide"
      width="extra-large"
      enabled={!!hasBranch}
      showExternalLink={!!hasBranch}
      icon={<BranchIcon width={12} height={12} color="white" />}
      text={hasBranch ? selectedBranch : t(I18nKey.COMMON$NO_BRANCH)}
    />
  );
}
