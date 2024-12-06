import ColdIcon from "./state-indicators/cold.svg?react";
import CoolingIcon from "./state-indicators/cooling.svg?react";
import FinishedIcon from "./state-indicators/finished.svg?react";
import RunningIcon from "./state-indicators/running.svg?react";
import WaitingIcon from "./state-indicators/waiting.svg?react";
import WarmIcon from "./state-indicators/warm.svg?react";

type SVGIcon = React.FunctionComponent<React.SVGProps<SVGSVGElement>>;
export type ProjectState =
  | "cold"
  | "cooling"
  | "finished"
  | "running"
  | "waiting"
  | "warm";

const INDICATORS: Record<ProjectState, SVGIcon> = {
  cold: ColdIcon,
  cooling: CoolingIcon,
  finished: FinishedIcon,
  running: RunningIcon,
  waiting: WaitingIcon,
  warm: WarmIcon,
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
