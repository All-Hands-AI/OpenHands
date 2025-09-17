import { useTranslation } from "react-i18next";

interface ResultSectionProps {
  content: string;
}

export function ResultSection({ content }: ResultSectionProps) {
  const { t } = useTranslation();

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-300">
          {t("TASK_TRACKING_OBSERVATION$RESULT")}
        </h3>
      </div>
      <div className="p-3 bg-gray-900 rounded-md overflow-auto text-gray-300 shadow-inner">
        <pre className="whitespace-pre-wrap text-sm">{content.trim()}</pre>
      </div>
    </div>
  );
}
