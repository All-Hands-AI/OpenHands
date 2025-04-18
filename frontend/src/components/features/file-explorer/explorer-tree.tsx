import { useTranslation } from "react-i18next";
import TreeNode from "./tree-node";
import { I18nKey } from "#/i18n/declaration";

interface ExplorerTreeProps {
  files: string[] | null;
  defaultOpen?: boolean;
}

export function ExplorerTree({
  files,
  defaultOpen = false,
}: ExplorerTreeProps) {
  const { t } = useTranslation();
  if (!files?.length) {
    const message = !files
      ? I18nKey.EXPLORER$LOADING_WORKSPACE_MESSAGE
      : I18nKey.EXPLORER$EMPTY_WORKSPACE_MESSAGE;
    return <div className="text-sm text-gray-400 pt-4">{t(message)}</div>;
  }
  return (
    <div className="w-full h-full pt-[4px]">
      {files.map((file) => (
        <TreeNode key={file} path={file} defaultOpen={defaultOpen} />
      ))}
    </div>
  );
}
