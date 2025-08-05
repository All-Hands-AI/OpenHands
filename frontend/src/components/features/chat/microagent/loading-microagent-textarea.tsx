import { useTranslation } from "react-i18next";
import { cn } from "#/utils/utils";

export function LoadingMicroagentTextarea() {
  const { t } = useTranslation();

  return (
    <textarea
      required
      disabled
      defaultValue=""
      placeholder={t("MICROAGENT$LOADING_PROMPT")}
      rows={6}
      className={cn(
        "bg-tertiary border border-[#717888] w-full rounded p-2 placeholder:italic placeholder:text-tertiary-alt resize-none",
        "disabled:bg-[#2D2F36] disabled:border-[#2D2F36] disabled:cursor-not-allowed",
      )}
    />
  );
}
