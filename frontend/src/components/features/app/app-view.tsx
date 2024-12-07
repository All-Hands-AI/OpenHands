export function AppView() {
  return (
    <div className="h-full w-full">
      <iframe
        src="http://localhost:4000"
        className="h-full w-full border-0"
        title="App"
      />
    </div>
  );
}