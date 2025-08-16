import CloseIcon from "#/icons/u-close.svg?react";

interface RemoveFileButtonProps {
  onClick: () => void;
}

export function RemoveFileButton({ onClick }: RemoveFileButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="flex w-4 h-4 rounded-full items-center justify-center bg-[#25272D] hover:bg-[#A1A1A1] cursor-pointer absolute top-1 right-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200"
    >
      <CloseIcon width={8} height={8} color="#ffffff" />
    </button>
  );
}
