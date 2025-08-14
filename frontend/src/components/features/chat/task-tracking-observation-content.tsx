import React from "react";
import ReactJsonView from "@microlink/react-json-view";
import { useTranslation } from "react-i18next";
import { TaskTrackingObservation } from "#/types/core/observations";
import { JSON_VIEW_THEME } from "#/utils/constants";

interface TaskTrackingObservationContentProps {
  event: TaskTrackingObservation;
}

export function TaskTrackingObservationContent({
  event,
}: TaskTrackingObservationContentProps) {
  const { t } = useTranslation();

  const { command, task_list: taskList } = event.extras;
  const shouldShowTaskList = command === "plan" && taskList.length > 0;

  // Parse the content as JSON if possible, otherwise use raw content
  let outputData: unknown;
  try {
    outputData = JSON.parse(event.content);
  } catch (e) {
    // If parsing fails, use the raw content
    outputData = event.content;
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "todo":
        return "⏳";
      case "in_progress":
        return "🔄";
      case "done":
        return "✅";
      default:
        return "❓";
    }
  };

  const getStatusClassName = (status: string) => {
    if (status === "done") {
      return "bg-green-800 text-green-200";
    }
    if (status === "in_progress") {
      return "bg-yellow-800 text-yellow-200";
    }
    return "bg-gray-700 text-gray-300";
  };

  return (
    <div className="flex flex-col gap-4">
      {/* Command section */}
      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-gray-300">
            {t("TASK_TRACKING_OBSERVATION$COMMAND")}
          </h3>
        </div>
        <div className="p-3 bg-gray-900 rounded-md overflow-auto text-gray-300 shadow-inner">
          <code className="text-blue-400">{command}</code>
        </div>
      </div>

      {/* Task List section - only show for 'plan' command */}
      {shouldShowTaskList && (
        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-gray-300">
              {t("TASK_TRACKING_OBSERVATION$TASK_LIST")} ({taskList.length}{" "}
              {taskList.length === 1 ? "item" : "items"})
            </h3>
          </div>
          <div className="p-3 bg-gray-900 rounded-md overflow-auto text-gray-300 max-h-[300px] shadow-inner">
            <div className="space-y-3">
              {taskList.map((task, index) => (
                <div key={task.id} className="border-l-2 border-gray-600 pl-3">
                  <div className="flex items-start gap-2">
                    <span className="text-lg">
                      {getStatusIcon(task.status)}
                    </span>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-gray-400">
                          {index + 1}.
                        </span>
                        <span
                          className={`text-xs px-2 py-1 rounded uppercase font-semibold ${getStatusClassName(
                            task.status,
                          )}`}
                        >
                          {task.status.replace("_", " ")}
                        </span>
                      </div>
                      <h4 className="font-medium text-white mt-1">
                        {task.title}
                      </h4>
                      <p className="text-xs text-gray-400 mt-1">{task.id}</p>
                      {task.notes && (
                        <p className="text-sm text-gray-300 mt-2 italic">
                          {task.notes}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Output section */}
      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-gray-300">
            {t("TASK_TRACKING_OBSERVATION$OUTPUT")}
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
              {event.content.trim() || t("OBSERVATION$TASK_TRACKING_NO_OUTPUT")}
            </pre>
          )}
        </div>
      </div>
    </div>
  );
}
