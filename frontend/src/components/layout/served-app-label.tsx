import { FaExternalLinkAlt } from "react-icons/fa";
import { useActivePort } from "#/hooks/query/use-active-port";

export function ServedAppLabel() {
  const { activePort } = useActivePort();

  return (
    <div className="flex items-center justify-between w-full">
      <div className="flex items-center gap-2">App</div>
      {!activePort && <span className="text-red-500">Offline</span>}
      {activePort && (
        <a
          href="http://localhost:4141"
          target="_blank"
          rel="noreferrer"
          className="flex items-center gap-2"
        >
          <span className="text-green-500">Online</span>
          <div className="flex items-center gap-1">
            <FaExternalLinkAlt fill="#a3a3a3" />
            <code className="text-xs">{activePort.split(":").pop()}</code>
          </div>
        </a>
      )}
    </div>
  );
}
