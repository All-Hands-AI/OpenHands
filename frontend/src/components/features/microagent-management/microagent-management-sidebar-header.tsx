import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import QuestionCircleIcon from "#/icons/question-circle.svg?react";

export function MicroagentManagementSidebarHeader() {
  const { t } = useTranslation();

  return (
    <div>
      <h1 className="text-white text-[28px] font-bold">
        {t(I18nKey.MICROAGENT_MANAGEMENT$DESCRIPTION)}
      </h1>
      <p className="text-white text-[14px] font-normal leading-[20px] pt-2">
        {t(I18nKey.MICROAGENT_MANAGEMENT$USE_MICROAGENTS)}
        <QuestionCircleIcon className="inline-block ml-1" />
      </p>
    </div>
  );
}
