import React, { useState } from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { cn } from "#/utils/utils";
import { code } from "../markdown/code";
import { ul, ol } from "../markdown/list";
import { paragraph } from "../markdown/paragraph";
import ArrowDown from "#/icons/angle-down-solid.svg?react";
import ArrowUp from "#/icons/angle-up-solid.svg?react";
import LightbulbIcon from "#/icons/lightbulb.svg?react";

interface ReasoningContentProps {
  content: string;
  className?: string;
}

export function ReasoningContent({
  content,
  className,
}: ReasoningContentProps) {
  // const { t } = useTranslation();
  const [isExpanded, setIsExpanded] = useState(false);

  if (!content || content.trim() === "") {
    return null;
  }

  return (
    <div
      className={cn(
        "border-l-2 border-blue-400 pl-3 my-2 bg-blue-50/50 rounded-r-md",
        className,
      )}
    >
      <button
        type="button"
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-2 text-sm font-medium text-blue-700 hover:text-blue-800 transition-colors cursor-pointer w-full text-left py-2"
      >
        <LightbulbIcon className="h-4 w-4 fill-blue-600" />
        <span>Reasoning</span>
        {isExpanded ? (
          <ArrowUp className="h-3 w-3 fill-blue-600 ml-auto" />
        ) : (
          <ArrowDown className="h-3 w-3 fill-blue-600 ml-auto" />
        )}
      </button>

      {isExpanded && (
        <div className="text-sm text-gray-700 pb-2 pr-2">
          <Markdown
            components={{
              code,
              ul,
              ol,
              p: paragraph,
            }}
            remarkPlugins={[remarkGfm]}
          >
            {content}
          </Markdown>
        </div>
      )}
    </div>
  );
}
