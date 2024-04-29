import { useColorMode } from "@docusaurus/theme-common";
import { Highlight, themes } from "prism-react-renderer";
import { useCopyToClipboard } from "react-use";

interface CodeBlockProps {
  language: string;
  code: string;
}

export function CodeBlock({ language, code }: CodeBlockProps) {
  const [state, copyToClipboard] = useCopyToClipboard();
  const { isDarkTheme } = useColorMode();

  const copyCode = () => {
    copyToClipboard(code);
  };

  return (
    <div
      style={{
        position: "relative",
      }}
    >
      <Highlight
        theme={isDarkTheme ? themes.vsLight : themes.vsDark}
        code={code}
        language={language}
      >
        {({ style, tokens, getLineProps, getTokenProps }) => (
          <pre style={style}>
            {tokens.map((line, i) => (
              <div key={i} {...getLineProps({ line })}>
                <span
                  style={{
                    display: "inline-block",
                    width: "3em",
                    color: "var(--gray)",
                  }}
                >
                  {i + 1}
                </span>
                {line.map((token, key) => (
                  <span key={key} {...getTokenProps({ token })} />
                ))}
              </div>
            ))}
          </pre>
        )}
      </Highlight>
      <button
        className="button button--secondary"
        style={{
          position: "absolute",
          top: "10px",
          right: "10px",
        }}
        onClick={copyCode}
      >
        {state.value ? "Copied!" : "Copy"}
      </button>
    </div>
  );
}
