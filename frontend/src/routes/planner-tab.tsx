import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import LessonPlanIcon from "#/icons/lesson-plan.svg?react";
import { useConversationStore } from "#/state/conversation-store";

function PlannerTab() {
  const { t } = useTranslation();
  const setConversationMode = useConversationStore(
    (state) => state.setConversationMode,
  );

  return (
    <div className="flex flex-col items-center justify-center w-full h-full p-10">
      <LessonPlanIcon width={109} height={109} color="#A1A1A1" />
      <span className="text-[#8D95A9] text-[19px] font-normal leading-5 pb-9">
        {t(I18nKey.PLANNER$EMPTY_MESSAGE)}
      </span>
      <button
        type="button"
        onClick={() => setConversationMode("plan")}
        className="flex w-[164px] h-[40px] p-2 justify-center items-center shrink-0 rounded-lg bg-white overflow-hidden text-black text-ellipsis font-sans text-[16px] not-italic font-normal leading-[20px] hover:cursor-pointer hover:opacity-80"
      >
        {t(I18nKey.COMMON$CREATE_A_PLAN)}
      </button>
    </div>
  );
}

export default PlannerTab;
