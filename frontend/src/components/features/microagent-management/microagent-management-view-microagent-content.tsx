import { useSelector } from "react-redux";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkBreaks from "remark-breaks";
import { code } from "../markdown/code";
import { ul, ol } from "../markdown/list";
import { paragraph } from "../markdown/paragraph";
import { anchor } from "../markdown/anchor";
import { RootState } from "#/store";

export function MicroagentManagementViewMicroagentContent() {
  const { selectedMicroagentItem } = useSelector(
    (state: RootState) => state.microagentManagement,
  );

  const { selectedRepository } = useSelector(
    (state: RootState) => state.microagentManagement,
  );

  const { microagent } = selectedMicroagentItem ?? {};

  const transformMicroagentContent = (): string => {
    if (!microagent) {
      return "";
    }

    // If no triggers exist, return the content as-is
    if (!microagent.triggers || microagent.triggers.length === 0) {
      return microagent.content;
    }

    // Create the triggers frontmatter
    const triggersFrontmatter = `
  ---

  triggers:
  ${microagent.triggers.map((trigger) => ` - ${trigger}`).join("\n")}

  ---
  `;

    // Prepend the frontmatter to the content
    return `
  ${triggersFrontmatter}

  ${microagent.content}
  `;
  };

  if (!microagent || !selectedRepository) {
    return null;
  }

  // Transform the content to include triggers frontmatter if applicable
  const transformedContent = transformMicroagentContent();

  return (
    <div className="w-full h-full p-6 bg-[#ffffff1a] rounded-2xl text-white text-sm">
      <Markdown
        components={{
          code,
          ul,
          ol,
          a: anchor,
          p: paragraph,
        }}
        remarkPlugins={[remarkGfm, remarkBreaks]}
      >
        {transformedContent}
      </Markdown>
    </div>
  );
}
