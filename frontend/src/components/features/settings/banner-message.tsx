interface BannerMessageProps {
  message: string;
}

export function BannerMessage({ message }: BannerMessageProps) {
  return (
    <div className="flex flex-col font-medium justify-center leading-[0] not-italic overflow-ellipsis overflow-hidden relative shrink-0 text-[12px] text-black text-nowrap">
      <p className="leading-[20px] overflow-ellipsis overflow-hidden whitespace-pre">
        {message}
      </p>
    </div>
  );
}
