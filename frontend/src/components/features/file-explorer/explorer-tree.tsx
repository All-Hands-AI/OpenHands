import { I18nKey } from "#/i18n/declaration"
import { useTranslation } from "react-i18next"
import TreeNode from "./tree-node"

interface ExplorerTreeProps {
  files: string[] | null
  defaultOpen?: boolean
  onClick?: () => void
}

export function ExplorerTree({
  files,
  defaultOpen = false,
  onClick,
}: ExplorerTreeProps) {
  const { t } = useTranslation()
  if (!files?.length) {
    const message = !files
      ? I18nKey.EXPLORER$LOADING_WORKSPACE_MESSAGE
      : I18nKey.EXPLORER$EMPTY_WORKSPACE_MESSAGE
    return <div className="pt-4 text-sm text-white">{t(message)}</div>
  }
  return (
    <div className="h-full w-full pt-[4px]">
      {files.map((file) => (
        <TreeNode
          key={file}
          path={file}
          defaultOpen={defaultOpen}
          onClick={onClick}
        />
      ))}
    </div>
  )
}
