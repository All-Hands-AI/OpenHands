import React from "react";
import ReactJsonView from "@microlink/react-json-view";
import { useTranslation } from "react-i18next";
import { JSON_VIEW_THEME } from "#/utils/constants";

interface MCPObservationContentProps {
  event: { message: string; arguments: Record<string, unknown> };
}

export function MCPObservationContent({ event }: MCPObservationContentProps) {
  const { t } = useTranslation();

  // Parse the content as JSON if possible
  let outputData: unknown;
  try {
    outputData = JSON.parse(event.message);
  } catch (e) {
    // If parsing fails, use the raw content
    outputData = event.message;
  }

  const hasArguments =
    event.arguments && Object.keys(event.arguments).length > 0;

  return (
    <div className="flex flex-col gap-4">
      {/* Arguments section */}
      {hasArguments && (
        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-gray-300">
              {t("MCP_OBSERVATION$ARGUMENTS")}
            </h3>
          </div>
          <div className="p-3 bg-gray-900 rounded-md overflow-auto text-gray-300 max-h-[200px] shadow-inner">
            <ReactJsonView
              name={false}
              src={event.arguments}
              theme={JSON_VIEW_THEME}
              collapsed={1}
              displayDataTypes={false}
            />
          </div>
        </div>
      )}

      {/* Output section */}
      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-gray-300">
            {t("MCP_OBSERVATION$OUTPUT")}
          </h3>
        </div>
        <div className="p-3 bg-gray-900 rounded-md overflow-auto text-gray-300 max-h-[300px] shadow-inner">
          {typeof outputData === "object" && outputData !== null ? (
            <ReactJsonView
              name={false}
              src={outputData}
              theme={JSON_VIEW_THEME}
              collapsed={1}
              displayDataTypes={false}
            />
          ) : (
            <pre className="whitespace-pre-wrap">
              {event.message.trim() || t("OBSERVATION$MCP_NO_OUTPUT")}
            </pre>
          )}
        </div>
      </div>
    </div>
  );
}
