import ColdIcon from "./state-indicators/cold.svg?react";
import RunningIcon from "./state-indicators/running.svg?react";

type SVGIcon = React.FunctionComponent<React.SVGProps<SVGSVGElement>>;
export type ProjectState = "RUNNING" | "STOPPED";

const INDICATORS: Record<ProjectState, SVGIcon> = {
  STOPPED: ColdIcon,
  RUNNING: RunningIcon,
};

interface ConversationStateIndicatorProps {
  state: ProjectState;
}

export function ConversationStateIndicator({
  state,
}: ConversationStateIndicatorProps) {
  const StateIcon = INDICATORS[state];

  return (
    <div data-testid={`${state}-indicator`}>
      <StateIcon />
    </div>
  );
}
