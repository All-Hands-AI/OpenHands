import React from "react";
import { useTranslation } from "react-i18next";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkBreaks from "remark-breaks";
import { I18nKey } from "#/i18n/declaration";
import LessonPlanIcon from "#/icons/lesson-plan.svg?react";
import { useConversationStore } from "#/state/conversation-store";
import { code } from "#/components/features/markdown/code";
import { ul, ol } from "#/components/features/markdown/list";
import { paragraph } from "#/components/features/markdown/paragraph";
import { anchor } from "#/components/features/markdown/anchor";
import {
  h1,
  h2,
  h3,
  h4,
  h5,
  h6,
} from "#/components/features/markdown/headings";
import { useScrollToBottom } from "#/hooks/use-scroll-to-bottom";

function PlannerTab() {
  const { t } = useTranslation();
  const { scrollRef: scrollContainerRef, onChatBodyScroll } = useScrollToBottom(
    React.useRef<HTMLDivElement>(null),
  );

  const { planContent, setConversationMode } = useConversationStore();

  if (planContent !== null && planContent !== undefined) {
    return (
      <div
        ref={scrollContainerRef}
        onScroll={(e) => onChatBodyScroll(e.currentTarget)}
        className="flex flex-col w-full h-full p-4 overflow-auto"
      >
        <Markdown
          components={{
            code,
            ul,
            ol,
            a: anchor,
            p: paragraph,
            h1,
            h2,
            h3,
            h4,
            h5,
            h6,
          }}
          remarkPlugins={[remarkGfm, remarkBreaks]}
        >
          {planContent}
        </Markdown>
      </div>
    );
  }

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
