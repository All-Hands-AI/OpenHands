import React from "react";
import { useTranslation } from "react-i18next";
import { GenericEventMessage } from "../generic-event-message";
import { TaskTrackingObservationContent } from "../task-tracking-observation-content";
import { ConfirmationButtons } from "#/components/shared/buttons/confirmation-buttons";
import { getObservationResult } from "../event-content-helpers/get-observation-result";
import { ObservationEvent, TaskTrackerObservation } from "#/types/v1/core";

interface TaskTrackingEventMessageProps {
  event: ObservationEvent<TaskTrackerObservation>;
  shouldShowConfirmationButtons: boolean;
}

export function TaskTrackingEventMessage({
  event,
  shouldShowConfirmationButtons,
}: TaskTrackingEventMessageProps) {
  const { t } = useTranslation();

  const { command, task_list: taskList, content } = event.observation;
  let title: React.ReactNode;
  let initiallyExpanded = false;

  // Determine title and expansion state based on command
  if (command === "plan") {
    title = t("OBSERVATION_MESSAGE$TASK_TRACKING_PLAN");
    initiallyExpanded = true;
  } else {
    // command === "view"
    title = t("OBSERVATION_MESSAGE$TASK_TRACKING_VIEW");
    initiallyExpanded = false;
  }

  return (
    <div>
      <GenericEventMessage
        title={title}
        details={
          <TaskTrackingObservationContent
            event={{
              command,
              taskList,
              content,
            }}
          />
        }
        success={getObservationResult(event)}
        initiallyExpanded={initiallyExpanded}
      />
      {shouldShowConfirmationButtons && <ConfirmationButtons />}
    </div>
  );
}
