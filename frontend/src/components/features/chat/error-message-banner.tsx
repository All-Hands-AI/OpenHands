import { Trans } from "react-i18next";
import i18n from "#/i18n";

interface ErrorMessageBannerProps {
  message: string;
}

export function ErrorMessageBanner({ message }: ErrorMessageBannerProps) {
  return (
    <div className="w-full rounded-lg p-2 text-black border border-red-800 bg-red-500">
      {i18n.exists(message) ? (
        <Trans
          i18nKey={message}
          components={{
            a: <span className="underline font-bold cursor-pointer">link</span>,
          }}
        />
      ) : (
        message
      )}
    </div>
  );
}
