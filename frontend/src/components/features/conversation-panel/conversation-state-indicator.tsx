import { ConversationStatus } from "#/types/conversation-status";
import ArchivedIcon from "./state-indicators/archived.svg?react";
import ErrorIcon from "./state-indicators/error.svg?react";
import RunningIcon from "./state-indicators/running.svg?react";
import StartingIcon from "./state-indicators/starting.svg?react";
import StoppedIcon from "./state-indicators/stopped.svg?react";

type SVGIcon = React.FunctionComponent<React.SVGProps<SVGSVGElement>>;

const CONVERSATION_STATUS_INDICATORS: Record<ConversationStatus, SVGIcon> = {
  STOPPED: StoppedIcon,
  RUNNING: RunningIcon,
  STARTING: StartingIcon,
  ARCHIVED: ArchivedIcon,
  ERROR: ErrorIcon,
};

interface ConversationStateIndicatorProps {
  conversationStatus: ConversationStatus;
}

export function ConversationStateIndicator({
  conversationStatus,
}: ConversationStateIndicatorProps) {
  const StateIcon = CONVERSATION_STATUS_INDICATORS[conversationStatus];

  return (
    <div data-testid={`${conversationStatus}-indicator`}>
      <StateIcon />
    </div>
  );
}
