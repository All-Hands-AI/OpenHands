import { useState } from "react";
import ArrowUp from "#/icons/angle-up-solid.svg?react";
import ArrowDown from "#/icons/angle-down-solid.svg?react";
import { BrowserSnapshot } from "./browser-snapshot";

interface CollapsibleBrowserOutputProps {
  url: string;
  screenshotSrc: string;
}

export function CollapsibleBrowserOutput({
  url,
  screenshotSrc,
}: CollapsibleBrowserOutputProps) {
  const [showDetails, setShowDetails] = useState(true);

  const imgSrc =
    screenshotSrc && screenshotSrc.startsWith("data:image/png;base64,")
      ? screenshotSrc
      : `data:image/png;base64,${screenshotSrc || ""}`;

  const arrowClasses = "h-4 w-4 ml-2 inline fill-neutral-300";

  return (
    <div className="flex gap-2 items-start justify-start border-l-2 pl-2 my-2 py-2 border-neutral-300">
      <div className="text-sm leading-4 flex flex-col gap-2 max-w-full">
        <p className="text-neutral-300 font-bold flex items-center">
          Browsed {url}
          <button
            type="button"
            onClick={() => setShowDetails(!showDetails)}
            className="cursor-pointer text-left"
          >
            {showDetails ? (
              <ArrowUp className={arrowClasses} />
            ) : (
              <ArrowDown className={arrowClasses} />
            )}
          </button>
        </p>
        {showDetails && screenshotSrc && (
          <div className="overflow-y-auto grow scrollbar-hide rounded-xl">
            <BrowserSnapshot src={imgSrc} />
          </div>
        )}
      </div>
    </div>
  );
}
