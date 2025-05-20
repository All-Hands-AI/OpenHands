interface ErrorMessageBannerProps {
  message: string;
}

export function ErrorMessageBanner({ message }: ErrorMessageBannerProps) {
  return (
    <div className="w-full rounded-lg p-2 text-black border border-red-800 bg-red-500">
      {message}
    </div>
  );
}
