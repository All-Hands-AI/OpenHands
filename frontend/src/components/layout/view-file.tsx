import TestFileViewer from "./RightSideContent/TestFileViewer"

import { FilesProvider } from "#/context/files"
import { FaFileInvoice, FaDownload, FaCopy } from "react-icons/fa"
import { IoClose } from "react-icons/io5"
import { useDispatch } from "react-redux"
import { setCurrentPathViewed } from "#/state/file-state-slice"
import { useListFile } from "#/hooks/query/use-list-file"
import { useEffect, useState } from "react"
import { FaCode } from "react-icons/fa6"
import { MdPreview } from "react-icons/md"
import Markdown from "react-markdown"
import remarkGfm from "remark-gfm"
import { code } from "#/components/features/markdown/code"
import { ol, ul } from "#/components/features/markdown/list"
import { anchor } from "#/components/features/markdown/anchor"

const ImagePreview = ({ src }: { src: string }) => (
  <div className="flex h-full w-full items-center justify-center p-4">
    <img
      src={src}
      alt="Preview"
      className="max-h-full max-w-full object-contain"
    />
  </div>
)

const PdfPreview = ({ src }: { src: string }) => (
  <div className="flex h-full w-full items-center justify-center p-4">
    <iframe
      src={src}
      className="h-full w-full rounded border"
      title="PDF viewer"
    />
  </div>
)

const MarkdownPreview = ({ content }: { content: string }) => (
  <div className="h-full w-full overflow-auto p-6">
    <div className="prose prose-sm max-w-none dark:prose-invert">
      <Markdown
        components={{
          code,
          ul,
          ol,
          a: anchor,
        }}
        remarkPlugins={[remarkGfm]}
      >
        {content}
      </Markdown>
    </div>
  </div>
)

const FilePreview = ({
  filePath,
  fileContent,
}: {
  filePath: string
  fileContent: string
}) => {
  const extension = filePath.split(".").pop()?.toLowerCase() || ""

  const createBlobUrl = () => {
    let mimeType = "text/plain"
    if (["jpg", "jpeg", "png", "gif", "webp"].includes(extension)) {
      mimeType = `image/${extension === "jpg" ? "jpeg" : extension}`
    } else if (extension === "pdf") {
      mimeType = "application/pdf"
    }

    const blob = new Blob([fileContent], { type: mimeType })
    return URL.createObjectURL(blob)
  }

  if (["jpg", "jpeg", "png", "gif", "webp"].includes(extension)) {
    return <ImagePreview src={createBlobUrl()} />
  } else if (extension === "pdf") {
    return <PdfPreview src={createBlobUrl()} />
  } else if (["html", "htm"].includes(extension)) {
    return (
      <div className="h-full w-full">
        <iframe
          srcDoc={fileContent}
          title="HTML Preview"
          className="h-full w-full border-none"
          sandbox="allow-scripts"
        />
      </div>
    )
  } else if (extension === "md") {
    return <MarkdownPreview content={fileContent} />
  }

  return (
    <div className="flex h-full w-full items-center justify-center">
      <div className="text-center">
        <p className="text-lg font-medium">Preview not available</p>
        <p className="text-sm text-gray-500">
          This file type cannot be previewed
        </p>
      </div>
    </div>
  )
}

const ViewFile = ({ currentPathViewed }: { currentPathViewed: string }) => {
  const dispatch = useDispatch()
  const isPreviewable = () => {
    if (!currentPathViewed) return false
    const extension = currentPathViewed.split(".").pop()?.toLowerCase() || ""
    return [
      "jpg",
      "jpeg",
      "png",
      "gif",
      "webp",
      "pdf",
      "html",
      "htm",
      "md",
    ].includes(extension)
  }

  const [viewMode, setViewMode] = useState<"code" | "preview">(
    isPreviewable() ? "preview" : "code",
  )
  const [copyStatus, setCopyStatus] = useState<"idle" | "copied">("idle")

  useEffect(() => {
    setViewMode(isPreviewable() ? "preview" : "code")
  }, [currentPathViewed])

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

  const handleCopyCode = async () => {
    if (!fileContent) return

    try {
      await navigator.clipboard.writeText(fileContent)
      setCopyStatus("copied")
      setTimeout(() => setCopyStatus("idle"), 2000)
    } catch (error) {
      console.error("Failed to copy:", error)
    }
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
        <div className="flex items-center gap-2">
          {isPreviewable() && (
            <div className="flex overflow-hidden rounded-md bg-neutral-900">
              <button
                onClick={() => setViewMode("code")}
                className={`flex items-center gap-1 px-3 py-1 text-sm hover:opacity-70 ${
                  viewMode === "code"
                    ? "bg-neutral-600 text-white"
                    : "bg-neutral-1000 text-neutral-100"
                }`}
                title="View code"
              >
                <FaCode size={14} className="flex-shrink-0" />
              </button>
              <button
                onClick={() => setViewMode("preview")}
                className={`flex items-center gap-1 px-3 py-1 text-sm hover:opacity-70 ${
                  viewMode === "preview"
                    ? "bg-neutral-600 text-white"
                    : "bg-neutral-1000 text-neutral-100"
                }`}
                title="View preview"
              >
                <MdPreview size={14} className="flex-shrink-0" />
              </button>
            </div>
          )}
          <button
            onClick={handleCopyCode}
            className="flex items-center gap-1 rounded bg-neutral-1000 px-3 py-1 text-sm text-neutral-100 hover:opacity-70"
            title="Copy code"
            disabled={!fileContent}
          >
            <FaCopy size={14} className="flex-shrink-0 fill-neutral-600" />
            {copyStatus === "copied" && (
              <span className="text-xs">Copied!</span>
            )}
          </button>
          <button
            onClick={handleDownload}
            className="flex items-center gap-1 rounded bg-neutral-1000 px-3 py-1 text-sm text-neutral-100 hover:opacity-70"
            title="Download file"
          >
            <FaDownload size={14} className="flex-shrink-0 fill-neutral-600" />
          </button>
        </div>
      </div>
      <div className="relative mt-3 h-full w-full overflow-auto rounded-lg border border-neutral-1000 p-1">
        <div className="absolute h-full w-full max-w-full overflow-hidden">
          {viewMode === "code" || !fileContent ? (
            <FilesProvider>
              <TestFileViewer currentPath={currentPathViewed} />
            </FilesProvider>
          ) : (
            <FilePreview
              filePath={currentPathViewed}
              fileContent={fileContent}
            />
          )}
        </div>
      </div>
    </div>
  )
}

export default ViewFile
