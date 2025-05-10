import React from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { code } from "../markdown/code";
import { ol, ul } from "../markdown/list";
import ArrowDown from "#/icons/angle-down-solid.svg?react";
import ArrowUp from "#/icons/angle-up-solid.svg?react";
import CheckCircle from "#/icons/check-circle-solid.svg?react";
import XCircle from "#/icons/x-circle-solid.svg?react";

interface SuccessIndicatorProps {
  success: boolean;
}

function SuccessIndicator({ success }: SuccessIndicatorProps) {
  return (
    <span className="flex-shrink-0">
      {success && (
        <CheckCircle
          data-testid="status-icon"
          className="h-4 w-4 ml-2 inline fill-success"
        />
      )}

      {!success && (
        <XCircle
          data-testid="status-icon"
          className="h-4 w-4 ml-2 inline fill-danger"
        />
      )}
    </span>
  );
}

interface GenericEventMessageProps {
  title: React.ReactNode;
  details: string;
  success?: boolean;
}

export function GenericEventMessage({
  title,
  details,
  success,
}: GenericEventMessageProps) {
  const [showDetails, setShowDetails] = React.useState(false);

  return (
    <div className="flex flex-col gap-2 border-l-2 pl-2 my-2 py-2 border-neutral-300 text-sm w-full">
      <div className="font-bold text-neutral-300">
        {title}
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

        {success !== undefined && <SuccessIndicator success={success} />}
      </div>

      {showDetails && (
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
      )}
    </div>
  );
}
