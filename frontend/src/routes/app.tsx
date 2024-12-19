import { useActiveHost } from "#/hooks/query/use-active-host";

function ServedApp() {
  const { activeHost } = useActiveHost();

  if (!activeHost) {
    return (
      <div className="flex items-center justify-center w-full h-full">
        <span className="text-4xl text-neutral-400 font-bold">
          Nothing to see here.
        </span>
      </div>
    );
  }

  return (
    <iframe title="Served App" src={activeHost} className="w-full h-full" />
  );
}

export default ServedApp;
