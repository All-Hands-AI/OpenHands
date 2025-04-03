import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Link } from "react-router";
import { I18nKey } from "#/i18n/declaration";
import { code } from "../markdown/code";
import { ol, ul } from "../markdown/list";
import ArrowUp from "#/icons/angle-up-solid.svg?react";
import ArrowDown from "#/icons/angle-down-solid.svg?react";
import CheckCircle from "#/icons/check-circle-solid.svg?react";
import XCircle from "#/icons/x-circle-solid.svg?react";
import { cn } from "#/utils/utils";
import { useConfig } from "#/hooks/query/use-config";

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
  const { data: config } = useConfig();
  const { t, i18n } = useTranslation();
  const [showDetails, setShowDetails] = useState(true);
  const [headline, setHeadline] = useState("");
  const [details, setDetails] = useState(message);

  useEffect(() => {
    // Check if the message is a translation key
    const isMessageTranslationKey =
      message &&
      message.includes("$") &&
      Object.values(I18nKey).includes(message as I18nKey);

    if (id && i18n.exists(id)) {
      setHeadline(t(id));

      // If the message is the same as the ID or is itself a translation key
      if (message === id || isMessageTranslationKey) {
        // Set details to the translated message instead of empty string
        // This ensures we show the proper translated text
        setDetails(t(id));
        // Don't show the expand/collapse button since it's redundant
        setShowDetails(false);
      } else {
        // Show the message as details
        setDetails(message);
        // Only show the expand/collapse button if there are actual details
        setShowDetails(message.length > 0);
      }
    } else if (isMessageTranslationKey && i18n.exists(message)) {
      // If the message itself is a translation key but wasn't passed as id
      setHeadline(t(message));
      setDetails(t(message));
      setShowDetails(false);
    }
  }, [id, message, i18n.language, t]);

  const statusIconClasses = "h-4 w-4 ml-2 inline";

  if (
    config?.FEATURE_FLAGS.ENABLE_BILLING &&
    config?.APP_MODE === "saas" &&
    id === I18nKey.STATUS$ERROR_LLM_OUT_OF_CREDITS
  ) {
    return (
      <div
        data-testid="out-of-credits"
        className="flex gap-2 items-center justify-start border-l-2 pl-2 my-2 py-2 border-danger"
      >
        <div className="text-sm w-full">
          <div className="font-bold text-danger">
            {t(I18nKey.STATUS$ERROR_LLM_OUT_OF_CREDITS)}
          </div>
          <Link
            className="mt-2 mb-2 w-full h-10 rounded flex items-center justify-center gap-2 bg-primary text-[#0D0F11]"
            to="/settings/billing"
          >
            {t(I18nKey.BILLING$CLICK_TO_TOP_UP)}
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div
      className={cn(
        "flex gap-2 items-center justify-start border-l-2 pl-2 my-2 py-2",
        type === "error" ? "border-danger" : "border-neutral-300",
      )}
    >
      <div className="text-sm w-full">
        <div className="flex flex-row justify-between items-center w-full">
          <span
            className={cn(
              headline ? "font-bold" : "",
              type === "error" ? "text-danger" : "text-neutral-300",
            )}
          >
            {headline && (
              <>
                {headline}
                {/* Only show the expand/collapse button if showDetails is true and there are details */}
                {details.length > 0 && showDetails !== false && (
                  <button
                    type="button"
                    onClick={() => setShowDetails(!showDetails)}
                    className="cursor-pointer text-left"
                  >
                    {showDetails ? (
                      <ArrowUp
                        className={cn(
                          "h-4 w-4 ml-2 inline",
                          type === "error" ? "fill-danger" : "fill-neutral-300",
                        )}
                      />
                    ) : (
                      <ArrowDown
                        className={cn(
                          "h-4 w-4 ml-2 inline",
                          type === "error" ? "fill-danger" : "fill-neutral-300",
                        )}
                      />
                    )}
                  </button>
                )}
              </>
            )}
          </span>
          {type === "action" && success !== undefined && (
            <span className="flex-shrink-0">
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
        {(!headline || showDetails) && (
          <div className="text-sm overflow-auto">
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
          </div>
        )}
      </div>
    </div>
  );
}
