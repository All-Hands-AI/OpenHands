import { useTranslation } from "react-i18next";
import { ContextMenu } from "../context-menu/context-menu";
import { ContextMenuListItem } from "../context-menu/context-menu-list-item";
import { ToolsContextMenuIconText } from "./tools-context-menu-icon-text";
import { useActiveConversation } from "#/hooks/query/use-active-conversation";
import { Provider } from "#/types/settings";
import {
  getGitPullPrompt,
  getGitPushPrompt,
  getCreatePRPrompt,
  getCreateNewBranchPrompt,
} from "#/utils/utils";

import ArrowUpIcon from "#/icons/u-arrow-up.svg?react";
import ArrowDownIcon from "#/icons/u-arrow-down.svg?react";
import PrIcon from "#/icons/u-pr.svg?react";
import CodeBranchIcon from "#/icons/u-code-branch.svg?react";
import { I18nKey } from "#/i18n/declaration";

const contextMenuListItemClassName =
  "cursor-pointer p-0 h-auto hover:bg-transparent px-[6px] !w-auto whitespace-nowrap";

interface GitToolsSubmenuProps {
  onClose: () => void;
  onSubmit: (message: string) => void;
}

export function GitToolsSubmenu({ onClose, onSubmit }: GitToolsSubmenuProps) {
  const { t } = useTranslation();
  const { data: conversation } = useActiveConversation();

  const currentGitProvider = conversation?.git_provider as Provider;

  const onGitPull = () => {
    onSubmit(getGitPullPrompt());
    onClose();
  };

  const onGitPush = () => {
    onSubmit(getGitPushPrompt(currentGitProvider));
    onClose();
  };

  const onCreatePR = () => {
    onSubmit(getCreatePRPrompt(currentGitProvider));
    onClose();
  };

  const onCreateNewBranch = () => {
    onSubmit(getCreateNewBranchPrompt());
    onClose();
  };

  return (
    <ContextMenu
      testId="git-tools-submenu"
      className="text-white bg-tertiary rounded-[6px] py-[6px] flex flex-col gap-2 w-max"
    >
      <ContextMenuListItem
        testId="git-pull-button"
        onClick={onGitPull}
        className={contextMenuListItemClassName}
      >
        <ToolsContextMenuIconText
          icon={<ArrowDownIcon width={16} height={16} />}
          text={t(I18nKey.COMMON$GIT_PULL)}
        />
      </ContextMenuListItem>

      <ContextMenuListItem
        testId="git-push-button"
        onClick={onGitPush}
        className={contextMenuListItemClassName}
      >
        <ToolsContextMenuIconText
          icon={<ArrowUpIcon width={16} height={16} />}
          text={t(I18nKey.COMMON$GIT_PUSH)}
        />
      </ContextMenuListItem>

      <ContextMenuListItem
        testId="create-pr-button"
        onClick={onCreatePR}
        className={contextMenuListItemClassName}
      >
        <ToolsContextMenuIconText
          icon={<PrIcon width={16} height={16} />}
          text={t(I18nKey.COMMON$CREATE_PR)}
        />
      </ContextMenuListItem>

      <ContextMenuListItem
        testId="create-new-branch-button"
        onClick={onCreateNewBranch}
        className={contextMenuListItemClassName}
      >
        <ToolsContextMenuIconText
          icon={<CodeBranchIcon width={16} height={16} />}
          text={t(I18nKey.COMMON$CREATE_NEW_BRANCH)}
        />
      </ContextMenuListItem>
    </ContextMenu>
  );
}
