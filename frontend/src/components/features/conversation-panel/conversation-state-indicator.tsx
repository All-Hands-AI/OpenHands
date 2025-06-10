import ColdIcon from "./state-indicators/cold.svg?react";
import RunningIcon from "./state-indicators/running.svg?react";

type SVGIcon = React.FunctionComponent<React.SVGProps<SVGSVGElement>>;
export type ProjectStatus =
  | "RUNNING"
  | "STOPPED"
  | "STARTING"
  | "CONNECTING"
  | "CONNECTED"
  | "DISCONNECTED";

type ProjectStatusWithIcon = Exclude<
  ProjectStatus,
  "CONNECTING" | "CONNECTED" | "DISCONNECTED"
>;

const INDICATORS: Record<ProjectStatusWithIcon, SVGIcon> = {
  STOPPED: ColdIcon,
  RUNNING: RunningIcon,
  STARTING: ColdIcon,
};

interface ConversationStateIndicatorProps {
  status: ProjectStatus;
}

export function ConversationStateIndicator({
  status,
}: ConversationStateIndicatorProps) {
  // @ts-expect-error - Type 'ProjectStatus' is not assignable to type 'ProjectStatusWithIcon'.
  const StateIcon = INDICATORS[status];

  return (
    <div data-testid={`${status}-indicator`}>
      <StateIcon />
    </div>
  );
}
