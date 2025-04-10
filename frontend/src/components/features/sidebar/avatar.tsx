import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";

interface AvatarProps {
  src: string;
}

export function Avatar({ src }: AvatarProps) {
  const { t } = useTranslation();
  return (
    <img
      src={src}
      alt="user avatar"
      className="w-full h-full rounded-full bg-gray-500"
    />
  );
}
