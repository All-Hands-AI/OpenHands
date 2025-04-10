import TestFileViewer from "./RightSideContent/TestFileViewer"

import { FilesProvider } from "#/context/files"
import { FaFileInvoice } from "react-icons/fa"
import { IoClose } from "react-icons/io5"
import { useDispatch } from "react-redux"
import { setCurrentPathViewed } from "#/state/file-state-slice"

const ViewFile = ({ currentPathViewed }: { currentPathViewed: string }) => {
  const dispatch = useDispatch()
  return (
    <div className="flex h-full max-h-[calc(100vh-30px)] w-full max-w-full flex-col overflow-hidden rounded-xl border border-neutral-1000 bg-white p-4">
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
      <div className="mt-3 w-full overflow-auto rounded-lg border border-neutral-1000 p-1">
        <div className="w-full max-w-full overflow-hidden">
          <FilesProvider>
            <TestFileViewer currentPath={currentPathViewed} />
          </FilesProvider>
        </div>
      </div>
    </div>
  )
}

export default ViewFile
