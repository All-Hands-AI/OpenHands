import { useUseCases } from "#/hooks/query/use-use-cases";
import StarIcon from "#/icons/star-icons.svg?react";
import { Link } from "react-router";

export function UseCaseList() {
  const { data: useCases } = useUseCases();

  return (
    <div className="grid mt-6 md:grid-cols-2 sm:grid-cols-2 grid-cols-1 gap-2 w-full">
      {(useCases?.results || []).map((item, key) => {
        return (
          <Link
            to={`/shares/conversations/${item.conversation_id}`}
            className="rounded-[12px] bg-transparent p-6 border border-gray-200 cursor-pointer hover:shadow-md hover:scale-105 transition-all ease-in duration-150"
            key={key}
          >
            <StarIcon className="mb-6" />
            <div className="flex items-center gap-2 mb-4">{item.title}</div>
            <div className="font-semibold text-[16px] text-tertiary">
              {item.title}
            </div>
          </Link>
        );
      })}
    </div>
  );
}
