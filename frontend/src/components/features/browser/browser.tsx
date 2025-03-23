import { BrowserSnapshot } from "./browser-snapshot";
import { EmptyBrowserMessage } from "./empty-browser-message";
import { useBrowser } from "#/hooks/query/use-browser";

export function BrowserPanel() {
  const { url, screenshotSrc } = useBrowser();

  // Debug log
  // eslint-disable-next-line no-console
  console.log("[Browser Debug] BrowserPanel rendering with:", {
    url,
    hasScreenshot: !!screenshotSrc,
    screenshotLength: screenshotSrc ? screenshotSrc.length : 0,
  });

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
        {screenshotSrc ? (
          <BrowserSnapshot src={imgSrc} />
        ) : (
          <EmptyBrowserMessage />
        )}
      </div>
    </div>
  );
}
