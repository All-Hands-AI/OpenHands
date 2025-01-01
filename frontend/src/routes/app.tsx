import { useActiveHost } from "#/hooks/query/use-active-host";

function ServedApp() {
  const { activeHost } = useActiveHost();

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
    <iframe title="Served App" src={activeHost} className="w-full h-full" />
  );
}

export default ServedApp;
