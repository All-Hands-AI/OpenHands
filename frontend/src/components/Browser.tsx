import React from "react";
import { useTranslation } from "react-i18next";
import { IoIosGlobe } from "react-icons/io";
import { useSelector } from "react-redux";
import { I18nKey } from "#/i18n/declaration";
import { RootState } from "#/store";

function Browser(): JSX.Element {
  const { t } = useTranslation();

  const { url, screenshotSrc } = useSelector(
    (state: RootState) => state.browser,
  );

  const imgSrc =
    screenshotSrc && screenshotSrc.startsWith("data:image/png;base64,")
      ? screenshotSrc
      : `data:image/png;base64,${screenshotSrc || ""}`;

  return (
    <div className="h-full w-full flex flex-col text-text-editor-base bg-bg-workspace">
      <div className="w-full p-2 truncate border-b border-border">{url}</div>
      <div className="overflow-y-auto grow scrollbar-hide rounded-xl">
        {screenshotSrc ? (
          <img
            src={imgSrc}
            style={{ objectFit: "contain", width: "100%", height: "auto" }}
            className="rounded-xl"
            alt="Browser Screenshot"
          />
        ) : (
          <div className="flex flex-col items-center h-full justify-center text-text-editor-active">
            <IoIosGlobe size={100} />
            {t(I18nKey.BROWSER$EMPTY_MESSAGE)}
          </div>
        )}
      </div>
    </div>
  );
}

export default Browser;
