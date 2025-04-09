import SyntaxHighlighter from 'react-syntax-highlighter';
import { oneLight as theme } from "react-syntax-highlighter/dist/cjs/styles/prism";

const CodeView = ({fileContent}) => {
  return (
  <SyntaxHighlighter
    language={'python'}
    style={theme}
    customStyle={{
      margin: 0,
      padding: "10px",
      height: "100%",
      fontSize: "0.875rem",
      borderRadius: 0,
    }}
  >
    {fileContent}
  </SyntaxHighlighter>
  )
}

export default CodeView
