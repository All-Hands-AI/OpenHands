import { RootState } from "#/store"
import { useSelector } from "react-redux"
import { BrowserSnapshot } from "./browser-snapshot"
import { EmptyBrowserMessage } from "./empty-browser-message"

export function BrowserPanel({ computerItem }: { computerItem?: any }) {
  const { url, screenshotSrc } = useSelector(
    (state: RootState) => state.browser,
  )

  const { url: browserUrl, screenshot } = computerItem?.extras || {
    url,
    screenshot: screenshotSrc,
  }

  const imgSrc =
    screenshot &&
    (screenshot.startsWith("data:image/png;base64,") ||
      screenshot.startsWith("data:image/jpeg;base64,"))
      ? screenshot
      : `data:image/png;base64,${screenshot || ""}`

  return (
    <div className="flex h-full w-full flex-col rounded text-neutral-400">
      <div className="grow overflow-y-auto rounded-xl scrollbar-hide">
        {screenshot ? (
          <BrowserSnapshot src={imgSrc} />
        ) : (
          <EmptyBrowserMessage />
        )}
      </div>
    </div>
  )
}
