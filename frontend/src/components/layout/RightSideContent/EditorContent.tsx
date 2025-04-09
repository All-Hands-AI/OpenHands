import { code } from "#/components/features/markdown/code";
import { ol, ul } from "#/components/features/markdown/list";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface EditorContentProps {
  computerItem: any;
}

const EditorContent = ({ computerItem }: EditorContentProps) => {
  const observation = computerItem?.observation;
  const textContent = computerItem?.extras?.diff || computerItem?.content;
  const detailContent = observation
    ? `\`\`\`diff\n${textContent}\n\`\`\``
    : `\`\`\`\n${textContent}\n\`\`\``;

  return (
    <div className="text-sm overflow-auto !w-[100%] !h-full">
      <Markdown
        components={{
          code,
          ul,
          ol,
        }}
        remarkPlugins={[remarkGfm]}
      >
        {detailContent}
      </Markdown>
    </div>
  );
};

export default EditorContent;
