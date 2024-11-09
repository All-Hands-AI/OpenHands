import { useTranslation } from "react-i18next";
import { IoIosGlobe } from "react-icons/io";
import { useSelector } from "react-redux";
import { Switch } from "@nextui-org/react";
import clsx from "clsx";
import { I18nKey } from "#/i18n/declaration";
import { RootState } from "#/store";
import { getSettings, saveSettings } from "#/services/settings";

function BrowserPanel() {
  const { t } = useTranslation();
  const settings = getSettings();

  const { url, screenshotSrc } = useSelector(
    (state: RootState) => state.browser,
  );

  const handleBrowserToggle = (enabled: boolean) => {
    saveSettings({ ...settings, ENABLE_BROWSING: enabled });
  };

  const imgSrc =
    screenshotSrc && screenshotSrc.startsWith("data:image/png;base64,")
      ? screenshotSrc
      : `data:image/png;base64,${screenshotSrc || ""}`;

  return (
    <div className="h-full w-full flex flex-col text-neutral-400">
      <div className="w-full p-2 truncate border-b border-neutral-600">
        {url}
      </div>
      <div className="overflow-y-auto grow scrollbar-hide rounded-xl">
        {!settings.ENABLE_BROWSING ? (
          <div className="flex flex-col items-center h-full justify-center gap-4 text-center px-4">
            <IoIosGlobe size={100} />
            <div>
              <p className="text-lg mb-2">Browser Control is Disabled</p>
              <p className="text-sm text-neutral-500">
                Browser control is an experimental feature that allows the AI assistant to interact with web browsers.
                To enable it, go to Settings and enable Browser Control.
              </p>
            </div>
          </div>
        ) : screenshotSrc ? (
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

export default BrowserPanel;
