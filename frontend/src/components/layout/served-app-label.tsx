import { FaExternalLinkAlt } from "react-icons/fa";
import { useActiveHost } from "#/hooks/query/use-active-host";

export function ServedAppLabel() {
  const { activeHost } = useActiveHost();

  function openAppInNewTab() {
    if (!activeHost) return;
    window.open(activeHost, "_blank");
  }

  return (
    <div className="flex items-center justify-between w-full">
      <div className="flex items-center gap-2">App</div>
      {activeHost && (
        <span onClick={openAppInNewTab} className="flex items-center gap-2">
          <div className="flex items-center gap-1">
            <FaExternalLinkAlt fill="#a3a3a3" />
          </div>
        </span>
      )}
    </div>
  );
}
