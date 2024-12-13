import { useServedApp } from "#/hooks/query/use-served-app";

function ServedApp() {
  const { isSuccess } = useServedApp();

  if (!isSuccess) {
    return (
      <div className="flex items-center justify-center w-full h-full">
        <span className="text-4xl text-neutral-400 font-bold">
          Nothing to see here.
        </span>
      </div>
    );
  }

  return (
    <iframe
      title="Served App"
      src="http://localhost:4141"
      className="w-full h-full"
    />
  );
}

export default ServedApp;
