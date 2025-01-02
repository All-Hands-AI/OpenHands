import React from "react";
import { FaArrowRotateRight } from "react-icons/fa6";
import { FaExternalLinkAlt } from "react-icons/fa";
import { useActiveHost } from "#/hooks/query/use-active-host";
import { PathForm } from "#/components/features/served-host/path-form";

function ServedApp() {
  const { activeHost } = useActiveHost();
  const [refreshKey, setRefreshKey] = React.useState(0);
  const [url, setUrl] = React.useState<string | null>(null);
  const [path, setPath] = React.useState<string>("hello");

  const formRef = React.useRef<HTMLFormElement>(null);

  const handleOnBlur = () => {
    if (formRef.current) {
      const formData = new FormData(formRef.current);
      const pathInputValue = formData.get("path")?.toString();

      setPath(pathInputValue || "");
    }
  };

  React.useEffect(() => {
    setUrl(activeHost);
    if (!activeHost) setPath("");
  }, [activeHost]);

  const fullUrl = `${url}/${path}`;

  if (!url) {
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
          className="text-sm"
        >
          <FaArrowRotateRight className="w-4 h-4" />
        </button>
        <button
          type="button"
          onClick={() => window.open(fullUrl, "_blank")}
          className="text-sm"
        >
          <FaExternalLinkAlt className="w-4 h-4" />
        </button>
        <div className="w-full flex">
          <span className="text-neutral-300">{url}/</span>
          <PathForm ref={formRef} onBlur={handleOnBlur} />
        </div>
      </div>
      <iframe
        key={refreshKey}
        title="Served App"
        src={fullUrl}
        className="w-full h-full"
      />
    </div>
  );
}

export default ServedApp;
