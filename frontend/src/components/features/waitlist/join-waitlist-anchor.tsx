import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";

export function JoinWaitlistAnchor() {
  const { t } = useTranslation();

  return (
    <a
      href="https://www.all-hands.dev/join-waitlist"
      target="_blank"
      rel="noreferrer"
      className="rounded bg-[#FFE165] text-black text-sm font-bold py-[10px] w-full text-center hover:opacity-80"
    >
      {t(I18nKey.WAITLIST$JOIN_WAITLIST)}
    </a>
  );
}
