import React from "react";
import { useTranslation } from "react-i18next";
import TreeNode from "./TreeNode";
import { I18nKey } from "#/i18n/declaration";

interface ExplorerTreeProps {
  files: string[];
  defaultOpen?: boolean;
}

function ExplorerTree({ files, defaultOpen = false }: ExplorerTreeProps) {
  const { t } = useTranslation();
  if (files.length === 0) {
    return (
      <div className="text-sm text-gray-400 pt-4">
        {t(I18nKey.EXPLORER$EMPTY_WORKSPACE_MESSAGE)}
      </div>
    );
  }
  return (
    <div className="w-full overflow-x-auto h-full pt-[4px]">
      {files.map((file) => (
        <TreeNode key={file} path={file} defaultOpen={defaultOpen} />
      ))}
    </div>
  );
}

export default ExplorerTree;
