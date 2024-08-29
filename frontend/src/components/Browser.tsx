import React from "react";
import { useTranslation } from "react-i18next";
import { IoIosGlobe } from "react-icons/io";
import { I18nKey } from "#/i18n/declaration";
import { useSession } from "#/context/session";

function Browser(): JSX.Element {
  const { t } = useTranslation();
  const { data } = useSession();

  const imgSrc =
    data.browseState?.extras.screenshot &&
    data.browseState.extras.screenshot.startsWith("data:image/png;base64,")
      ? data.browseState.extras.screenshot
      : `data:image/png;base64,${data.browseState?.extras.screenshot || ""}`;

  return (
    <div className="h-full w-full flex flex-col text-neutral-400">
      <div className="w-full p-2 truncate border-b border-neutral-600">
        {data.browseState?.extras.url}
      </div>
      <div className="overflow-y-auto grow scrollbar-hide rounded-xl">
        {data.browseState?.extras.screenshot ? (
          <img
            src={imgSrc}
            style={{ objectFit: "contain", width: "100%", height: "auto" }}
            className="rounded-xl"
            alt="Browser Screenshot"
          />
        ) : (
          <div className="flex flex-col items-center h-full justify-center">
            <IoIosGlobe size={100} />
            {t(I18nKey.BROWSER$EMPTY_MESSAGE)}
          </div>
        )}
      </div>
    </div>
  );
}

export default Browser;
