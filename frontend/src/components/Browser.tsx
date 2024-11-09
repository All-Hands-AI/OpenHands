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
      <div className="w-full p-2 flex items-center justify-between border-b border-neutral-600">
        <div className="truncate">{url}</div>
        <Switch
          name="enable-browsing"
          defaultSelected={settings.ENABLE_BROWSING}
          onValueChange={handleBrowserToggle}
          classNames={{
            thumb: clsx(
              "bg-[#5D5D5D] w-3 h-3",
              "group-data-[selected=true]:bg-white",
            ),
            wrapper: clsx(
              "border border-[#D4D4D4] bg-white px-[6px] w-12 h-6",
              "group-data-[selected=true]:border-transparent group-data-[selected=true]:bg-[#4465DB]",
            ),
            label: "text-[#A3A3A3] text-xs",
          }}
        >
          Browser Control
        </Switch>
      </div>
      <div className="overflow-y-auto grow scrollbar-hide rounded-xl">
        {screenshotSrc ? (
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
