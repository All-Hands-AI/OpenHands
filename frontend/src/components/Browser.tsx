import React from "react";
import { useTranslation } from "react-i18next";
import { IoIosGlobe } from "react-icons/io";
import { I18nKey } from "#/i18n/declaration";
import { useSession } from "#/context/session";

const isBrowseObservation = (message: object): message is BrowseObservation =>
  "observation" in message && message.observation === "browse";

function Browser(): JSX.Element {
  const { t } = useTranslation();
  const { eventLog } = useSession();
  const [browseState, setBrowseState] = React.useState<BrowseObservation>();

  React.useEffect(() => {
    const browseObservation = eventLog
      .map((msg) => JSON.parse(msg))
      .find(isBrowseObservation);

    if (browseObservation) {
      setBrowseState(browseObservation);
    }
  }, [eventLog]);

  const imgSrc =
    browseState?.extras.screenshot &&
    browseState.extras.screenshot.startsWith("data:image/png;base64,")
      ? browseState.extras.screenshot
      : `data:image/png;base64,${browseState?.extras.screenshot || ""}`;

  return (
    <div className="h-full w-full flex flex-col text-neutral-400">
      <div className="w-full p-2 truncate border-b border-neutral-600">
        {browseState?.extras.url}
      </div>
      <div className="overflow-y-auto grow scrollbar-hide rounded-xl">
        {browseState?.extras.screenshot ? (
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
