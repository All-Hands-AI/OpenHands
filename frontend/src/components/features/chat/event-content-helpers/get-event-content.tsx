import { Trans } from "react-i18next";
import { MonoComponent } from "../mono-component";
import { PathComponent } from "../path-component";
import { getActionContent } from "./get-action-content";
import { getObservationContent } from "./get-observation-content";
import i18n from "#/i18n";
import {
  ActionEvent,
  ExecuteBashAction,
  ExecuteBashObservation,
  ObservationEvent,
  OpenHandsEvent,
  StrReplaceEditorAction,
  StrReplaceEditorObservation,
} from "#/types/v1/core";
import { isActionEvent, isObservationEvent } from "#/types/v1/type-guards";

const isStrReplaceEditorAction = (
  event: ActionEvent,
): event is ActionEvent<StrReplaceEditorAction> =>
  event.action.kind === "StrReplaceEditorAction";

const isExecuteBashAction = (
  event: ActionEvent,
): event is ActionEvent<ExecuteBashAction> =>
  event.action.kind === "ExecuteBashAction";

const isStrReplaceEditorObservation = (
  event: ObservationEvent,
): event is ObservationEvent<StrReplaceEditorObservation> =>
  event.observation.kind === "StrReplaceEditorObservation";

const isExecuteBashActionObservation = (
  event: ObservationEvent,
): event is ObservationEvent<ExecuteBashObservation> =>
  event.observation.kind === "ExecuteBashObservation";

const trimText = (text: string, maxLength: number): string => {
  if (!text) return "";
  return text.length > maxLength ? `${text.substring(0, maxLength)}...` : text;
};

export const getEventContent = (event: OpenHandsEvent) => {
  let title: React.ReactNode = "";
  let details: string = "";

  if (isActionEvent(event)) {
    const actionKey = `ACTION_MESSAGE$${event.action.kind.toUpperCase()}`;

    // If translation key exists, use Trans component
    if (i18n.exists(actionKey)) {
      title = (
        <Trans
          i18nKey={actionKey}
          values={{
            path: isStrReplaceEditorAction(event) && event.action.path,
            command:
              isExecuteBashAction(event) && trimText(event.action.command, 80),
            mcp_tool_name:
              event.action.kind === "MCPToolAction" && event.action.data.name,
          }}
          components={{
            path: <PathComponent />,
            cmd: <MonoComponent />,
          }}
        />
      );
    } else {
      // For generic actions, just use the uppercase type
      title = event.action.kind.toUpperCase();
    }
    details = getActionContent(event);
  }

  if (isObservationEvent(event)) {
    const observationKey = `OBSERVATION_MESSAGE$${event.observation.kind.toUpperCase()}`;

    // If translation key exists, use Trans component
    if (i18n.exists(observationKey)) {
      title = (
        <Trans
          i18nKey={observationKey}
          values={{
            path:
              isStrReplaceEditorObservation(event) && event.observation.path,
            command:
              isExecuteBashActionObservation(event) &&
              event.observation.command &&
              trimText(event.observation.command, 80),
            mcp_tool_name:
              event.observation.kind === "MCPToolObservation" &&
              event.observation.tool_name,
          }}
          components={{
            path: <PathComponent />,
            cmd: <MonoComponent />,
          }}
        />
      );
    } else {
      // For generic observations, just use the uppercase type
      title = event.observation.kind.toUpperCase();
    }
    details = getObservationContent(event);
  }

  return {
    title: title ?? i18n.t("EVENT$UNKNOWN_EVENT"),
    details: details ?? i18n.t("EVENT$UNKNOWN_EVENT"),
  };
};
