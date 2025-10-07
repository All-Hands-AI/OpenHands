import { InputSkeleton } from "../input-skeleton";
import { SubtextSkeleton } from "../subtext-skeleton";

export function GitSettingInputsSkeleton() {
  return (
    <div className="px-11 py-9 flex flex-col gap-12">
      <div className="flex flex-col gap-6">
        <InputSkeleton />
        <SubtextSkeleton />
      </div>

      <div className="flex flex-col gap-6">
        <InputSkeleton />
        <SubtextSkeleton />
      </div>
    </div>
  );
}
