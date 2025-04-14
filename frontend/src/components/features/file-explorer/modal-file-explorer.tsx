import { useState, useEffect } from "react"
import QRCode from "qrcode"
import {
  useGetJwt,
  useGetListAddresses,
  usePersistActions,
} from "#/zutand-stores/persist-config/selector"
import { reduceString } from "#/utils/utils"
import OpenHands from "#/api/open-hands"
import { useAccount } from "wagmi"
import { useListFiles } from "#/hooks/query/use-list-files"
import { ExplorerTree } from "./explorer-tree"
import TreeNode from "./tree-node"

interface Token {
  name: string
  icon: string
  coinGeckoId: string
}

interface Network {
  chainId: string
  name: string
  icon: string
}

interface FileExplorerModalProps {
  isOpen: boolean
  onClose: () => void
  filePath?: string
}

const FileExplorerModal = ({
  isOpen,
  onClose,
  filePath,
}: FileExplorerModalProps) => {
  const {
    data: files,
    refetch: refetchFiles,
    error,
  } = useListFiles({
    isCached: false,
    enabled: true,
  })
  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-[51] flex items-center justify-center">
      <div
        className="fixed inset-0 bg-gray-300/50 backdrop-blur-sm"
        onClick={onClose}
      />

      <div className="relative w-full max-w-lg overflow-hidden rounded-xl border border-neutral-1000 bg-white shadow-2xl dark:border-gray-500/30 dark:bg-gray-300">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-b-neutral-1000 bg-white px-6 py-4 dark:border-gray-500/20 dark:bg-gray-300">
          <h2 className="flex items-center text-xl font-semibold text-neutral-100 dark:text-content">
            All files in this task
          </h2>
          <button
            onClick={onClose}
            className="rounded-lg p-2 text-neutral-800 transition-colors hover:bg-neutral-1000 hover:text-neutral-100 dark:text-tertiary-light"
          >
            <svg
              className="h-5 w-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {filePath ? (
          <div className="p-6">
            {/* <div>All file in folder: {filePath}</div> */}
            <TreeNode
              key={`all-file-in-${filePath}`}
              path={filePath}
              defaultOpen
              onClick={onClose}
            />
          </div>
        ) : (
          <div className="p-6">
            {!error && <ExplorerTree files={files || []} onClick={onClose} />}
          </div>
        )}
      </div>
    </div>
  )
}

export default FileExplorerModal
