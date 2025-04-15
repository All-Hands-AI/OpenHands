import { Editor } from "@monaco-editor/react"

interface McpViewProps {
  content: string
}

const McpView = ({ content }: McpViewProps) => {
  const renderValue = () => {
    let value
    try {
      const parsedContent =
        typeof content === "string" ? JSON.parse(content) : content
      value = parsedContent
    } catch (error) {
      value = content
    }
    return value
  }

  return (
    <Editor
      height="100%"
      width="100%"
      language="markdown"
      value={renderValue()}
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
