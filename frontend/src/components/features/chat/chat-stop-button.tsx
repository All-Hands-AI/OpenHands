import PauseIcon from "#/icons/pause.svg?react";

export interface ChatStopButtonProps {
  handleStop: () => void;
}

export function ChatStopButton({ handleStop }: ChatStopButtonProps) {
  return (
    <button type="button" onClick={handleStop} data-testid="stop-button">
      <PauseIcon className="block max-w-none w-4 h-4" />
    </button>
  );
}
