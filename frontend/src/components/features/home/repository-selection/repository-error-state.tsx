import { useTranslation } from "react-i18next";
import { cn } from "#/utils/utils";

export interface RepositoryErrorStateProps {
  wrapperClassName?: string;
}

export function RepositoryErrorState({
  wrapperClassName,
}: RepositoryErrorStateProps) {
  const { t } = useTranslation();
  return (
    <div
      data-testid="repo-dropdown-error"
      className={cn(
        "flex items-center gap-2 max-w-[500px] h-10 px-3 bg-tertiary border border-[#717888] rounded-sm text-red-500",
        wrapperClassName,
      )}
    >
      <span className="text-sm">{t("HOME$FAILED_TO_LOAD_REPOSITORIES")}</span>
    </div>
  );
}
