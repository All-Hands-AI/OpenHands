import { Trans } from "react-i18next";
import i18n from "#/i18n";

interface ErrorMessageBannerProps {
  message: string;
  billingUrl?: string;
}

export function ErrorMessageBanner({
  message,
  billingUrl = "https://app.all-hands.dev/billing",
}: ErrorMessageBannerProps) {
  return (
    <div className="w-full rounded-lg p-2 text-black border border-red-800 bg-red-500">
      {i18n.exists(message) ? (
        <Trans
          i18nKey={message}
          components={{
            a: (
              <a
                className="underline font-bold cursor-pointer"
                href={billingUrl}
                target="_blank"
                rel="noopener noreferrer"
              >
                link
              </a>
            ),
          }}
        />
      ) : (
        message
      )}
    </div>
  );
}
