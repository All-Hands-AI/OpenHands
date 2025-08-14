import { useTranslation } from "react-i18next";
import { useDispatch } from "react-redux";
import { ContextMenu } from "../context-menu/context-menu";
import { ContextMenuListItem } from "../context-menu/context-menu-list-item";
import { ToolsContextMenuIconText } from "./tools-context-menu-icon-text";

import TachometerFastIcon from "#/icons/tachometer-fast.svg?react";
import PrStatusIcon from "#/icons/pr-status.svg?react";
import DocumentIcon from "#/icons/document.svg?react";
import WaterIcon from "#/icons/u-water.svg?react";
import { I18nKey } from "#/i18n/declaration";
import { setMessageToSend } from "#/state/conversation-slice";
import { REPO_SUGGESTIONS } from "#/utils/suggestions/repo-suggestions";

const contextMenuListItemClassName =
  "cursor-pointer p-0 h-auto hover:bg-transparent px-[6px] !w-auto whitespace-nowrap";

interface MacrosSubmenuProps {
  onClose: () => void;
}

export function MacrosSubmenu({ onClose }: MacrosSubmenuProps) {
  const { t } = useTranslation();
  const dispatch = useDispatch();

  const onIncreaseTestCoverage = () => {
    dispatch(setMessageToSend(REPO_SUGGESTIONS.INCREASE_TEST_COVERAGE));
    onClose();
  };
  const onFixReadme = () => {
    dispatch(setMessageToSend(REPO_SUGGESTIONS.FIX_README));
    onClose();
  };
  const onAutoMergePRs = () => {
    dispatch(setMessageToSend(REPO_SUGGESTIONS.AUTO_MERGE_PRS));
    onClose();
  };
  const onCleanDependencies = () => {
    dispatch(setMessageToSend(REPO_SUGGESTIONS.CLEAN_DEPENDENCIES));
    onClose();
  };

  return (
    <ContextMenu
      testId="macros-submenu"
      className="text-white bg-tertiary rounded-[6px] py-[6px] px-1 flex flex-col gap-2 overflow-visible"
    >
      <ContextMenuListItem
        testId="increase-test-coverage-button"
        onClick={onIncreaseTestCoverage}
        className={contextMenuListItemClassName}
      >
        <ToolsContextMenuIconText
          icon={<TachometerFastIcon width={16} height={16} />}
          text={t(I18nKey.INCREASE_TEST_COVERAGE)}
        />
      </ContextMenuListItem>

      <ContextMenuListItem
        testId="fix-readme-button"
        onClick={onFixReadme}
        className={contextMenuListItemClassName}
      >
        <ToolsContextMenuIconText
          icon={<DocumentIcon width={16} height={16} />}
          text={t(I18nKey.FIX_README)}
        />
      </ContextMenuListItem>

      <ContextMenuListItem
        testId="auto-merge-prs-button"
        onClick={onAutoMergePRs}
        className={contextMenuListItemClassName}
      >
        <ToolsContextMenuIconText
          icon={<PrStatusIcon width={16} height={16} />}
          text={t(I18nKey.AUTO_MERGE_PRS)}
        />
      </ContextMenuListItem>

      <ContextMenuListItem
        testId="clean-dependencies-button"
        onClick={onCleanDependencies}
        className={contextMenuListItemClassName}
      >
        <ToolsContextMenuIconText
          icon={<WaterIcon width={16} height={16} />}
          text={t(I18nKey.CLEAN_DEPENDENCIES)}
        />
      </ContextMenuListItem>
    </ContextMenu>
  );
}
