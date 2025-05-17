import Markdown from "react-markdown";
import SyntaxHighlighter from "react-syntax-highlighter";
import { atomOneDark } from "react-syntax-highlighter/dist/esm/styles/hljs";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { JupyterLine } from "#/utils/parse-cell-content";
import { paragraph } from "../markdown/paragraph";
import { ImageCarousel } from "../images/image-carousel";

interface JupyterCellOutputProps {
  lines: JupyterLine[];
}

export function JupyterCellOutput({ lines }: JupyterCellOutputProps) {
  const { t } = useTranslation();
  return (
    <div className="rounded-lg bg-gray-800 dark:bg-gray-900 p-2 text-xs">
      <div className="mb-1 text-gray-400">
        {t(I18nKey.JUPYTER$OUTPUT_LABEL)}
      </div>
      <pre
        className="scrollbar-custom scrollbar-thumb-gray-500 hover:scrollbar-thumb-gray-400 dark:scrollbar-thumb-white/10 dark:hover:scrollbar-thumb-white/20 overflow-auto px-5 max-h-[60vh] bg-gray-800"
        style={{ padding: 0, marginBottom: 0, fontSize: "0.75rem" }}
      >
        {/* display the lines as plaintext or image */}
        {lines.map((line, index) => {
          if (line.type === "image") {
            // If we have a direct URL to the image, use ImageCarousel
            if (line.url) {
              return (
                <div key={index} className="my-2">
                  <ImageCarousel size="medium" images={[line.url]} />
                </div>
              );
            }
            // Otherwise fall back to the markdown rendering of base64 image
            return (
              <div key={index}>
                <Markdown
                  components={{
                    p: paragraph,
                  }}
                  urlTransform={(value: string) => value}
                >
                  {line.content}
                </Markdown>
              </div>
            );
          }
          return (
            <div key={index}>
              <SyntaxHighlighter language="plaintext" style={atomOneDark}>
                {line.content}
              </SyntaxHighlighter>
            </div>
          );
        })}
      </pre>
    </div>
  );
}
