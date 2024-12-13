import { FaExternalLinkAlt } from "react-icons/fa";
import { useServedApp } from "#/hooks/query/use-served-app";

export function ServedAppLabel() {
  const { isSuccess, isPending } = useServedApp();

  return (
    <div className="flex items-center justify-between w-full">
      <div className="flex items-center gap-2">
        App
        {isPending && (
          <div className="animate-pulse w-2 h-2 rounded-full bg-yellow-400" />
        )}
      </div>
      {!isSuccess && <span className="text-red-500">Offline</span>}
      {isSuccess && (
        <a
          href="http://localhost:4141"
          target="_blank"
          rel="noreferrer"
          className="flex items-center gap-2"
        >
          <span className="text-green-500">Online</span>
          <FaExternalLinkAlt fill="#a3a3a3" />
        </a>
      )}
    </div>
  );
}
