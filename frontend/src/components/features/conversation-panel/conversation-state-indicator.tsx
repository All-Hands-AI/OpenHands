import ColdIcon from "./state-indicators/cold.svg?react";
import RunningIcon from "./state-indicators/running.svg?react";

type SVGIcon = React.FunctionComponent<React.SVGProps<SVGSVGElement>>;
export type ProjectStatus = "RUNNING" | "STOPPED" | "STARTING";

const INDICATORS: Record<ProjectStatus, SVGIcon> = {
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
  const StateIcon = INDICATORS[status];

  return (
    <div data-testid={`${status}-indicator`}>
      <StateIcon />
    </div>
  );
}
