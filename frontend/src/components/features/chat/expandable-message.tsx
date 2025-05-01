import { PayloadAction } from "@reduxjs/toolkit";
import { useEffect, useState } from "react";
import { Trans, useTranslation } from "react-i18next";
import Markdown from "react-markdown";
import { Link } from "react-router";
import remarkGfm from "remark-gfm";
import { useConfig } from "#/hooks/query/use-config";
import { I18nKey } from "#/i18n/declaration";
import ArrowDown from "#/icons/angle-down-solid.svg?react";
import ArrowUp from "#/icons/angle-up-solid.svg?react";
import CheckCircle from "#/icons/check-circle-solid.svg?react";
import XCircle from "#/icons/x-circle-solid.svg?react";
import { OpenHandsAction } from "#/types/core/actions";
import { OpenHandsObservation } from "#/types/core/observations";
import { cn } from "#/utils/utils";
import { code } from "../markdown/code";
import { ol, ul } from "../markdown/list";
import { MonoComponent } from "./mono-component";
import { PathComponent } from "./path-component";

const trimText = (text: string, maxLength: number): string => {
  if (!text) return "";
  return text.length > maxLength ? `${text.substring(0, maxLength)}...` : text;
};

interface ExpandableMessageProps {
  id?: string;
  message: string;
  type: string;
  success?: boolean;
  observation?: PayloadAction<OpenHandsObservation>;
  action?: PayloadAction<OpenHandsAction>;
}

export function ExpandableMessage({
  id,
  message,
  type,
  success,
  observation,
  action,
}: ExpandableMessageProps) {
  const { data: config } = useConfig();
  const { t, i18n } = useTranslation();
  const [i18nReady, setI18nReady] = useState(i18n.isInitialized);

  const [showDetails, setShowDetails] = useState(true);
  const [details, setDetails] = useState(message);
  const [translationId, setTranslationId] = useState<string | undefined>(id);
  const [translationParams, setTranslationParams] = useState<
    Record<string, unknown>
  >({
    observation,
    action,
  });

  // Listen for i18n initialization
  useEffect(() => {
    if (!i18nReady) {
      const handleInitialized = () => {
        setI18nReady(true);
      };

      if (i18n.isInitialized) {
        setI18nReady(true);
        return undefined;
      }
      i18n.on("initialized", handleInitialized);
      return () => {
        i18n.off("initialized", handleInitialized);
      };
    }
    return undefined;
  }, [i18n, i18nReady]);

  useEffect(() => {
    // Only process translations when i18n is ready or for non-critical messages
    if (!id) {
      setTranslationId(undefined);
      setDetails(message);
      return;
    }

    // For RECALL messages, wait until i18n is ready
    if (id === I18nKey.OBSERVATION_MESSAGE$RECALL && !i18nReady) {
      // Don't set anything yet, wait for i18n to be ready
      return;
    }

    // For other messages or when i18n is ready
    if (i18n.exists(id)) {
      let processedObservation = observation;
      let processedAction = action;

      if (action && action.payload.action === "run") {
        const trimmedCommand = trimText(action.payload.args.command, 80);
        processedAction = {
          ...action,
          payload: {
            ...action.payload,
            args: {
              ...action.payload.args,
              command: trimmedCommand,
            },
          },
        };
      }

      if (observation && observation.payload.observation === "run") {
        const trimmedCommand = trimText(observation.payload.extras.command, 80);
        processedObservation = {
          ...observation,
          payload: {
            ...observation.payload,
            extras: {
              ...observation.payload.extras,
              command: trimmedCommand,
            },
          },
        };
      }

      setTranslationId(id);
      setTranslationParams({
        observation: processedObservation,
        action: processedAction,
      });
      setDetails(message);
      setShowDetails(false);
    } else {
      // If no translation exists, just use the message
      setTranslationId(undefined);
      setDetails(message);
    }
  }, [id, message, observation, action, i18n.language, i18nReady]);

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
              "font-bold",
              type === "error" ? "text-danger" : "text-neutral-300",
            )}
          >
            {(() => {
              // If we're waiting for i18n to be ready for RECALL message, show loading
              if (id === I18nKey.OBSERVATION_MESSAGE$RECALL && !i18nReady) {
                return null; // Don't render anything until i18n is ready
              }

              // If no translation ID, just show the message
              if (!translationId) {
                return message;
              }

              // If i18n is ready and the translation exists, use Trans component
              if (i18n.exists(translationId)) {
                return (
                  <Trans
                    i18nKey={translationId}
                    values={translationParams}
                    components={{
                      bold: <strong />,
                      path: <PathComponent />,
                      cmd: <MonoComponent />,
                    }}
                  />
                );
              }

              // Fallback to the message
              return message;
            })()}
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
        {showDetails && (
          <div className="text-sm">
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
