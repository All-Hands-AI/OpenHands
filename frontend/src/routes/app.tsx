import React from "react";
import { FaArrowRotateRight } from "react-icons/fa6";
import { useActiveHost } from "#/hooks/query/use-active-host";

function ServedApp() {
  const { activeHost } = useActiveHost();
  const [refreshKey, setRefreshKey] = React.useState(0);

  if (!activeHost) {
    return (
      <div className="flex items-center justify-center w-full h-full p-10">
        <span className="text-neutral-400 font-bold">
          If you tell OpenHands to start a web server, the app will appear here.
        </span>
      </div>
    );
  }

  return (
    <div className="h-full w-full">
      <div className="w-full p-2 flex items-center gap-4 border-b border-neutral-600">
        <button
          type="button"
          onClick={() => setRefreshKey((prev) => prev + 1)}
          className="rounded bg-neutral-700 hover:bg-neutral-600 text-sm"
        >
          <FaArrowRotateRight className="w-4 h-4" />
        </button>
        <a
          href={activeHost}
          target="_blank"
          rel="noopener noreferrer"
          className="text-neutral-300 hover:text-white cursor-pointer"
        >
          {activeHost}
        </a>
      </div>
      <iframe
        key={refreshKey}
        title="Served App"
        src={activeHost}
        className="w-full h-full"
      />
    </div>
  );
}

export default ServedApp;
