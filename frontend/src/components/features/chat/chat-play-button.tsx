import PlayIcon from "#/icons/play-solid.svg?react";

export interface ChatResumeAgentButtonProps {
  onAgentResumed: () => void;
}

export function ChatResumeAgentButton({
  onAgentResumed,
}: ChatResumeAgentButtonProps) {
  return (
    <button type="button" onClick={onAgentResumed} data-testid="play-button">
      <PlayIcon className="block max-w-none w-4 h-4" />
    </button>
  );
}
