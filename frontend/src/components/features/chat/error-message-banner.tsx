import { Trans } from "react-i18next";
import { isTranslationKey } from "#/utils/is-translation-key";

interface ErrorMessageBannerProps {
  message: string;
}

export function ErrorMessageBanner({ message }: ErrorMessageBannerProps) {
  const isTransKey = isTranslationKey(message);

  return (
    <div className="w-full rounded-lg p-2 text-black border border-red-800 bg-red-500">
      {isTransKey ? (
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
