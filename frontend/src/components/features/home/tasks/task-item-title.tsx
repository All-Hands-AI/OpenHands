export function TaskItemTitle({ children: title }: React.PropsWithChildren) {
  return (
    <div className="py-3">
      <h3 className="text-[16px] leading-6 font-[500]">{title}</h3>
    </div>
  );
}
