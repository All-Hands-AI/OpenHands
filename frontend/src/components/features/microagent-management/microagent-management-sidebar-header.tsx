import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { QuestionCircle } from "#/assets/question-circle";

export function MicroagentManagementSidebarHeader() {
  const { t } = useTranslation();

  return (
    <div>
      <h1 className="text-white text-[28px] font-bold">
        {t(I18nKey.MICROAGENT_MANAGEMENT$DESCRIPTION)}
      </h1>
      <p className="text-white text-[14px] font-normal leading-[20px] pt-2">
        {t(I18nKey.MICROAGENT_MANAGEMENT$USE_MICROAGENTS)}
        <QuestionCircle
          width={16}
          height={16}
          active
          className="inline-flex ml-1"
        />
      </p>
    </div>
  );
}
