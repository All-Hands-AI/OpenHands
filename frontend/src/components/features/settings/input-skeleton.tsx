export function InputSkeleton() {
  return (
    <div className="flex flex-col gap-2.5">
      <div className="w-[70px] h-[20px] skeleton" />
      <div className="w-[680px] h-[40px] skeleton" />
    </div>
  );
}
