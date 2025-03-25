import { useTranslation } from "react-i18next";

interface AvatarProps {
  src: string;
}

export function Avatar({ src }: AvatarProps) {
  const { t } = useTranslation();
  return (
    <img
      src={src}
      alt={t("AVATAR$ALT_TEXT")}
      className="w-full h-full rounded-full"
    />
  );
}
