import { useActivePort } from "#/hooks/query/use-active-port";

function ServedApp() {
  const { activePort } = useActivePort();

  if (!activePort) {
    return (
      <div className="flex items-center justify-center w-full h-full">
        <span className="text-4xl text-neutral-400 font-bold">
          Nothing to see here.
        </span>
      </div>
    );
  }

  return (
    <iframe title="Served App" src={activePort} className="w-full h-full" />
  );
}

export default ServedApp;
