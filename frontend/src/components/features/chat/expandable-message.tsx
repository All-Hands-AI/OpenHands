import { useConfig } from "#/hooks/query/use-config";
import ArrowDown from "#/icons/angle-down-solid.svg?react";
import ArrowUp from "#/icons/angle-up-solid.svg?react";
import CheckCircle from "#/icons/check-circle-solid.svg?react";
import XCircle from "#/icons/x-circle-solid.svg?react";
import { HANDLED_ACTIONS } from "#/state/chat-slice";
import { OpenHandsEventType } from "#/types/core/base";
import { cn } from "#/utils/utils";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import Markdown from "react-markdown";
import { Link } from "react-router";
import remarkGfm from "remark-gfm";
import { code } from "../markdown/code";
import { ol, ul } from "../markdown/list";
import MessageActionDisplay from "./message-action-display";
interface ExpandableMessageProps {
  id?: string;
  message: string;
  type: string;
  success?: boolean;
  messageActionID?: string;
}

export function ExpandableMessage({
  id,
  message,
  type,
  success,
  messageActionID,
}: ExpandableMessageProps) {
  const { data: config } = useConfig();
  const { t, i18n } = useTranslation();
  const [showDetails, setShowDetails] = useState(true);
  const [headline, setHeadline] = useState("");
  const [details, setDetails] = useState(message);

  useEffect(() => {
    if (id && i18n.exists(id)) {
      setHeadline(t(id) + ` (${messageActionID})`);
      setDetails(message);
      setShowDetails(true);
    }
  }, [id, message, i18n.language]);

  const statusIconClasses = "h-4 w-4 mr-2 inline";

  if (
    config?.FEATURE_FLAGS.ENABLE_BILLING &&
    config?.APP_MODE === "saas" &&
    id === "STATUS$ERROR_LLM_OUT_OF_CREDITS"
  ) {
    return (
      <div
        data-testid="out-of-credits"
        className="my-2 flex items-center justify-start gap-2 border-l-2 border-danger py-2 pl-2"
      >
        <div className="w-full text-sm">
          <div className="font-bold text-danger">
            {t("STATUS$ERROR_LLM_OUT_OF_CREDITS")}
          </div>
          <Link
            className="mb-2 mt-2 flex h-10 w-full items-center justify-center gap-2 rounded bg-primary text-[#0D0F11]"
            to="/settings/billing"
          >
            {t("BILLING$CLICK_TO_TOP_UP")}
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div
      className={cn(
        "flex items-center justify-start gap-2 py-2",
        type === "error" ? "border-danger" : "border-neutral-300",
      )}
    >
      <div className="w-full text-sm">
        <div className="flex w-full flex-row items-center">
          {/* {type === "action" && success === undefined && (
            <span className="flex-shrink-0">
              <div className="w-4 h-4 mr-2 rounded-full bg-neutral-100"></div>
            </span>
          )} */}
          {type === "action" && success !== undefined && (
            <span className="flex-shrink-0">
              {success ? (
                <CheckCircle
                  data-testid="status-icon"
                  className={cn(statusIconClasses, "fill-neutral-700")}
                />
              ) : (
                <XCircle
                  data-testid="status-icon"
                  className={cn(statusIconClasses, "fill-neutral-700")}
                />
              )}
            </span>
          )}
          <span
            className={cn(
              headline ? "font-bold" : "",
              type === "error"
                ? "text-danger"
                : "text-neutral-600 dark:text-white",
            )}
          >
            {headline && (
              <>
                {headline}
                <button
                  type="button"
                  onClick={() => setShowDetails(!showDetails)}
                  className="cursor-pointer text-left"
                >
                  {showDetails ? (
                    <ArrowUp
                      className={cn(
                        "ml-2 inline h-4 w-4",
                        type === "error" ? "fill-danger" : "fill-neutral-700",
                      )}
                    />
                  ) : (
                    <ArrowDown
                      className={cn(
                        "ml-2 inline h-4 w-4",
                        type === "error" ? "fill-danger" : "fill-neutral-700",
                      )}
                    />
                  )}
                </button>
              </>
            )}
          </span>
        </div>
        {(!headline || showDetails) && (
          <div className="flex text-sm">
            <div className="relative w-6 shrink-0">
              {/* <div className="border-l border-dashed border-neutral-300 absolute start-[7px] top-0 bottom-2"></div> */}
            </div>
            <div className="flex-1 overflow-auto">
              {type === "action" &&
              HANDLED_ACTIONS.includes(
                messageActionID as OpenHandsEventType,
              ) ? (
                <MessageActionDisplay
                  messageActionID={messageActionID}
                  content={details}
                />
              ) : (
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
          </div>
        )}
      </div>
    </div>
  );
}
