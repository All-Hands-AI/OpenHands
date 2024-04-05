import React from "react";
import { useTranslation } from "react-i18next";
import assistantAvatar from "../../assets/assistant-avatar.png";
import { I18nKey } from "../../i18n/declaration";

function InitializingStatus(): JSX.Element {
  const { t } = useTranslation();

  return (
    <div className="flex items-center m-auto h-full">
      <img
        src={assistantAvatar}
        alt="assistant avatar"
        className="w-[40px] h-[40px] mx-2.5"
      />
      <div>{t(I18nKey.CHAT_INTERFACE$INITIALZING_AGENT_LOADING_MESSAGE)}</div>
    </div>
  );
}

export default InitializingStatus;
