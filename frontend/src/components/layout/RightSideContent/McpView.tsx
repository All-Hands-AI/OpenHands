import { Editor } from "@monaco-editor/react"
import { useMemo } from "react"

interface McpViewProps {
  content: string | null | undefined | object
}

const McpView = ({ content }: McpViewProps) => {
  const value = useMemo(() => {
    if (typeof content !== "string") {
      return String(content ?? "")
    }

    try {
      const parsedContent = JSON.parse(content)
      return typeof parsedContent === "string"
        ? parsedContent
        : JSON.stringify(parsedContent, null, 2)
    } catch (error) {
      return content
    }
  }, [content])

  return (
    <Editor
      height="100%"
      width="100%"
      language="markdown"
      value={value}
      options={{
        readOnly: true,
        domReadOnly: true,
        minimap: { enabled: false },
        lineNumbers: "off",
        lineDecorationsWidth: 0,
        scrollBeyondLastLine: false,
        scrollbar: {
          vertical: "hidden",
          horizontal: "hidden",
        },
        fontSize: 14,
        wordWrap: "on",
        folding: false,
        quickSuggestions: false,
        contextmenu: false,
        hideCursorInOverviewRuler: true,
        overviewRulerBorder: false,
        overviewRulerLanes: 0,
      }}
    />
  )
}

export default McpView
