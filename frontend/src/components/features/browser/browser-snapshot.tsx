import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";

interface BrowserSnaphsotProps {
  src: string;
}

export function BrowserSnapshot({ src }: BrowserSnaphsotProps) {
  const { t } = useTranslation();

  return (
    <img
      src={src}
      style={{ objectFit: "contain", width: "100%", height: "auto" }}
      className="rounded-xl"
      alt={t(I18nKey.BROWSER$SCREENSHOT_ALT)}
    />
  );
}
