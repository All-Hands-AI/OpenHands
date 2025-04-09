import { RootState } from "#/store";
import { useSelector } from "react-redux";
import { BrowserSnapshot } from "./browser-snapshot";
import { EmptyBrowserMessage } from "./empty-browser-message";

export function BrowserPanel({ computerItem }: { computerItem: any }) {
  const { url, screenshotSrc } = useSelector(
    (state: RootState) => state.browser,
  );

  const { url: browserUrl, screenshot } = computerItem?.extras || {
    url,
    screenshot: screenshotSrc,
  };

  const imgSrc =
    screenshot && screenshot.startsWith("data:image/png;base64,")
      ? screenshot
      : `data:image/png;base64,${screenshot || ""}`;

  return (
    <div className="h-full w-full flex flex-col text-neutral-400 rounded">
      <div className="w-full p-3 bg-neutral-800 truncate border-b border-gray-200 rounded-t-lg">
        {browserUrl}
      </div>
      <div className="overflow-y-auto grow scrollbar-hide rounded-xl">
        {screenshot ? (
          <BrowserSnapshot src={imgSrc} />
        ) : (
          <EmptyBrowserMessage />
        )}
      </div>
    </div>
  );
}
