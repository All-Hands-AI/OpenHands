export function CountBadge({ count }: { count: number }) {
  return (
    <span className="text-[11px] leading-5 text-root-primary bg-neutral-400 px-1 rounded-xl">
      {count}
    </span>
  );
}
