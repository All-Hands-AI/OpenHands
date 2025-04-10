import TestFileViewer from "./RightSideContent/TestFileViewer"

import { FilesProvider } from "#/context/files"
import { FaFileInvoice, FaDownload } from "react-icons/fa"
import { IoClose } from "react-icons/io5"
import { useDispatch } from "react-redux"
import { setCurrentPathViewed } from "#/state/file-state-slice"
import { useListFile } from "#/hooks/query/use-list-file"

const ViewFile = ({ currentPathViewed }: { currentPathViewed: string }) => {
  const dispatch = useDispatch()
  const { data: fileContent } = useListFile({
    path: currentPathViewed,
    enabled: !!currentPathViewed,
  })

  const handleDownload = () => {
    if (!fileContent || !currentPathViewed) return

    const blob = new Blob([fileContent], { type: "text/plain" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = currentPathViewed.split("/").pop() || "file.txt"
    document.body.appendChild(a)
    a.click()
    URL.revokeObjectURL(url)
    document.body.removeChild(a)
  }

  return (
    <div className="flex h-full max-h-[calc(100vh-30px)] w-full max-w-full flex-col overflow-hidden rounded-xl border border-neutral-1000 bg-white p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-5">
          <div
            className="cursor-pointer"
            onClick={() => dispatch(setCurrentPathViewed(""))}
          >
            <IoClose className="h-5 w-5" />
          </div>
          <div className="flex items-center gap-2 overflow-hidden">
            <FaFileInvoice className="h-4 w-4 flex-shrink-0 fill-blue-500" />
            <div className="line-clamp-1 overflow-hidden text-ellipsis text-sm">
              {currentPathViewed}
            </div>
          </div>
        </div>
        <button
          onClick={handleDownload}
          className="flex items-center gap-1 rounded bg-neutral-1000 px-3 py-1 text-sm text-neutral-100"
          title="Download file"
        >
          <FaDownload size={12} className="flex-shrink-0" />
          <span>Download</span>
        </button>
      </div>
      <div className="relative mt-3 h-full w-full overflow-auto rounded-lg border border-neutral-1000 p-1">
        <div className="absolute h-full w-full max-w-full overflow-hidden">
          <FilesProvider>
            <TestFileViewer currentPath={currentPathViewed} />
          </FilesProvider>
        </div>
      </div>
    </div>
  )
}

export default ViewFile
