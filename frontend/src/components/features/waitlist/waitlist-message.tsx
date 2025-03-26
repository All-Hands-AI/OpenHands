import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";

interface WaitlistMessageProps {
  content: "waitlist" | "sign-in";
}

export function WaitlistMessage({ content }: WaitlistMessageProps) {
  const { t } = useTranslation();

  return (
    <div className="flex flex-col gap-2 w-full items-center text-center">
      <h1 className="text-2xl font-bold">
        {content === "sign-in" && t(I18nKey.AUTH$SIGN_IN_WITH_GITHUB)}
        {content === "waitlist" && t(I18nKey.WAITLIST$ALMOST_THERE)}
      </h1>
      {content === "sign-in" && (
        <p>
          {t(I18nKey.LANDING$OR)}{" "}
          <a
            href="https://www.all-hands.dev/join-waitlist"
            target="_blank"
            rel="noreferrer noopener"
            className="text-blue-500 hover:underline underline-offset-2"
          >
            {t(I18nKey.WAITLIST$JOIN)}
          </a>{" "}
          {t(I18nKey.WAITLIST$IF_NOT_JOINED)}
        </p>
      )}
      {content === "waitlist" && (
        <p className="text-sm">{t(I18nKey.WAITLIST$PATIENCE_MESSAGE)}</p>
      )}
    </div>
  );
}
