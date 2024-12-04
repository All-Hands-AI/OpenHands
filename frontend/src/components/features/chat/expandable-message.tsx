import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { code } from "../markdown/code";
import { ol, ul } from "../markdown/list";
import ArrowUp from "#/icons/angle-up-solid.svg?react";
import ArrowDown from "#/icons/angle-down-solid.svg?react";

interface ExpandableMessageProps {
  id?: string;
  message: string;
  type: string;
}

export function ExpandableMessage({
  id,
  message,
  type,
}: ExpandableMessageProps) {
  const { t, i18n } = useTranslation();
  const [showDetails, setShowDetails] = useState(true);
  const [headline, setHeadline] = useState("");
  const [details, setDetails] = useState(message);

  useEffect(() => {
    if (id && i18n.exists(id)) {
      setHeadline(t(id));
      setDetails(message);
      setShowDetails(false);
    }
  }, [id, message, i18n.language]);

  const border = type === "error" ? "border-danger" : "border-neutral-300";
  const textColor = type === "error" ? "text-danger" : "text-neutral-300";
  let arrowClasses = "h-4 w-4 ml-2 inline";
  if (type === "error") {
    arrowClasses += " fill-danger";
  } else {
    arrowClasses += " fill-neutral-300";
  }

  return (
    <div
      className={`flex gap-2 items-center justify-start border-l-2 pl-2 my-2 py-2 ${border}`}
    >
      <div className="text-sm leading-4 flex flex-col gap-2 max-w-full">
        {headline && (
          <p className={`${textColor} font-bold`}>
            {headline}
            <button
              type="button"
              onClick={() => setShowDetails(!showDetails)}
              className="cursor-pointer text-left"
            >
              {showDetails ? (
                <ArrowUp className={arrowClasses} />
              ) : (
                <ArrowDown className={arrowClasses} />
              )}
            </button>
          </p>
        )}
        {showDetails && (
          <Markdown
            className="text-sm overflow-auto"
            components={{
              code,
              ul,
              ol,
            }}
            remarkPlugins={[remarkGfm]}
          >
            {details}
          </Markdown>
        )}
      </div>
    </div>
  );
}
