export function AppSettingsInputsSkeleton() {
  return (
    <div
      data-testid="app-settings-skeleton"
      className="px-11 py-9 flex flex-col gap-6"
    >
      <div className="flex flex-col gap-2.5">
        <div className="w-[70px] h-[20px] skeleton" />
        <div className="w-[680px] h-[40px] skeleton" />
      </div>

      <div className="flex items-center gap-2">
        <div className="w-[48px] h-[24px] skeleton-round" />
        <div className="w-[100px] h-[20px] skeleton" />
      </div>

      <div className="flex items-center gap-2">
        <div className="w-[48px] h-[24px] skeleton-round" />
        <div className="w-[100px] h-[20px] skeleton" />
      </div>
    </div>
  );
}
