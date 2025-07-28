import PauseIcon from "#/icons/pause.svg?react";

export interface ChatStopButtonProps {
  handleStop: () => void;
}

export function ChatStopButton({ handleStop }: ChatStopButtonProps) {
  return (
    <div
      className="bg-[#959cb2] box-border content-stretch flex flex-row gap-[3px] items-center justify-center overflow-clip px-0.5 py-1 relative rounded-[100px] shrink-0 size-6 transition-all duration-200 hover:bg-[#a5abc2] active:scale-95 cursor-pointer"
      onClick={handleStop}
      data-testid="stop-button"
    >
      <PauseIcon className="block max-w-none size-full" />
    </div>
  );
}
