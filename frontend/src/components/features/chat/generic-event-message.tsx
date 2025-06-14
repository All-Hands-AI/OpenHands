import React from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { code } from "../markdown/code";
import { ol, ul } from "../markdown/list";
import ArrowDown from "#/icons/angle-down-solid.svg?react";
import ArrowUp from "#/icons/angle-up-solid.svg?react";
import { SuccessIndicator } from "./success-indicator";
import { ObservationResultStatus } from "./event-content-helpers/get-observation-result";

interface GenericEventMessageProps {
  title: React.ReactNode;
  details: string | React.ReactNode;
  success?: ObservationResultStatus;
}

export function GenericEventMessage({
  title,
  details,
  success,
}: GenericEventMessageProps) {
  const [showDetails, setShowDetails] = React.useState(false);

  return (
    <div className="flex flex-col gap-2 border-l-2 pl-2 my-2 py-2 border-neutral-300 text-sm w-full">
      <div className="flex items-center justify-between font-bold text-neutral-300">
        <div>
          {title}
          {details && (
            <button
              type="button"
              onClick={() => setShowDetails((prev) => !prev)}
              className="cursor-pointer text-left"
            >
              {showDetails ? (
                <ArrowUp className="h-4 w-4 ml-2 inline fill-neutral-300" />
              ) : (
                <ArrowDown className="h-4 w-4 ml-2 inline fill-neutral-300" />
              )}
            </button>
          )}
        </div>

        {success && <SuccessIndicator status={success} />}
      </div>

      {showDetails &&
        (typeof details === "string" ? (
          <Markdown
            components={{
              code,
              ul,
              ol,
            }}
            remarkPlugins={[remarkGfm]}
          >
            {details}
          </Markdown>
        ) : (
          details
        ))}
    </div>
  );
}
