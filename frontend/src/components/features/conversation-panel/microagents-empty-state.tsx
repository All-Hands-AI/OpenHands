import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { Typography } from "#/ui/typography";

interface MicroagentsEmptyStateProps {
  isError: boolean;
}

export function MicroagentsEmptyState({ isError }: MicroagentsEmptyStateProps) {
  const { t } = useTranslation();

  return (
    <div className="flex items-center justify-center h-full p-4">
      <Typography.Text className="text-gray-400">
        {isError
          ? t(I18nKey.MICROAGENTS_MODAL$FETCH_ERROR)
          : t(I18nKey.CONVERSATION$NO_MICROAGENTS)}
      </Typography.Text>
    </div>
  );
}
