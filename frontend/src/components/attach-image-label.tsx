import Clip from "#/icons/clip.svg?react";

export function AttachImageLabel() {
  return (
    <div className="flex self-start items-center text-[#A3A3A3] text-xs leading-[18px] -tracking-[0.08px] cursor-pointer">
      <Clip width={16} height={16} />
      Attach images
    </div>
  );
}
