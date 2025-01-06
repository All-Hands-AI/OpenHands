import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { code } from "../markdown/code";
import { ol, ul } from "../markdown/list";
import ArrowUp from "#/icons/angle-up-solid.svg?react";
import ArrowDown from "#/icons/angle-down-solid.svg?react";
import CheckCircle from "#/icons/check-circle-solid.svg?react";
import XCircle from "#/icons/x-circle-solid.svg?react";
import { cn } from "#/utils/utils";

interface ExpandableMessageProps {
  id?: string;
  message: string;
  type: string;
  success?: boolean;
}

export function ExpandableMessage({
  id,
  message,
  type,
  success,
}: ExpandableMessageProps) {
  const { t, i18n } = useTranslation();
  const [showDetails, setShowDetails] = useState(true);
  const [headline, setHeadline] = useState("");
  const [details, setDetails] = useState(message);

  useEffect(() => {
    if (id && i18n.exists(id)) {
      // Only show the headline if the action hasn't been executed yet (success is undefined)
      if (success === undefined) {
        setHeadline(t(id));
        setDetails("");
        setShowDetails(false);
      } else {
        // Only show the details if the action has been executed
        setHeadline("");
        setDetails(message);
        setShowDetails(true);
      }
    } else {
      // If no translation ID is provided, just show the message
      setHeadline("");
      setDetails(message);
      setShowDetails(true);
    }
  }, [id, message, success, i18n.language, t]);

  const statusIconClasses = "h-4 w-4 ml-2 inline";

  return (
    <div
      className={cn(
        "flex gap-2 items-center justify-start border-l-2 pl-2 my-2 py-2",
        type === "error" ? "border-danger" : "border-neutral-300",
      )}
    >
      <div className="text-sm w-full">
        {headline ? (
          // Show headline for unexecuted actions
          <div className="flex flex-row justify-between items-center w-full">
            <span
              className={cn(
                "font-bold",
                type === "error" ? "text-danger" : "text-neutral-300",
              )}
            >
              {headline}
            </span>
          </div>
        ) : (
          // Show details for executed actions
          <div className="flex flex-row justify-between items-center w-full">
            <div className="flex-grow">
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
            </div>
            {type === "action" && success !== undefined && (
              <span className="flex-shrink-0 ml-2">
                {success ? (
                  <CheckCircle
                    data-testid="status-icon"
                    className={cn(statusIconClasses, "fill-success")}
                  />
                ) : (
                  <XCircle
                    data-testid="status-icon"
                    className={cn(statusIconClasses, "fill-danger")}
                  />
                )}
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
