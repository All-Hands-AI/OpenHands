import { useCasesMocks } from "#/mocks/use-cases.mock";
import { useTranslation } from "react-i18next";
import StarIcon from "#/icons/star-icons.svg?react";
import { Link } from "react-router";
import { useUseCases } from "#/hooks/query/use-use-cases";

export function UseCaseList() {
  const { t } = useTranslation();
  const { data: useCases } = useUseCases();

  console.log("useCases", useCases);

  return (
    <div className="grid mt-6 md:grid-cols-2 sm:grid-cols-2 grid-cols-1 gap-2 w-full">
      {Object.entries(useCasesMocks).map(([k, itemValue], key) => {
        const titleQuestion = itemValue.find((x: any) => x.source === "user");

        return (
          <Link
            to={`/shares/conversations/${k}`}
            className="rounded-[12px] bg-transparent p-6 border border-gray-200 cursor-pointer hover:shadow-md hover:scale-105 transition-all ease-in duration-150"
            key={key}
          >
            <StarIcon className="mb-6" />
            <div className="flex items-center gap-2 mb-4">
              {titleQuestion.message.slice(0, 10).toUpperCase()}
            </div>
            <div className="font-semibold text-[16px] text-tertiary">
              {titleQuestion.message}
            </div>
          </Link>
        );
      })}
    </div>
  );
}
