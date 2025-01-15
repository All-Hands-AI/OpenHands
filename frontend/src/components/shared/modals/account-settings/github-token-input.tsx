import { cn, Tooltip } from "@nextui-org/react";
import { useTranslation } from "react-i18next";
import { FaCircleXmark } from "react-icons/fa6";
import { I18nKey } from "#/i18n/declaration";

interface GitHubTokenInputProps {
  isSet: boolean;
  onUnset: () => void;
}

export function GitHubTokenInput({ isSet, onUnset }: GitHubTokenInputProps) {
  const { t } = useTranslation();

  return (
    <label
      data-testid="github-token"
      htmlFor="ghToken"
      className="flex flex-col gap-2"
    >
      <div className="flex items-center gap-1">
        <span
          className={cn(
            "text-[11px] leading-4 font-bold uppercase border px-1 rounded",
            !isSet
              ? "border-red-800 bg-red-500"
              : "border-green-800 bg-green-500",
          )}
        >
          {isSet ? "set" : "unset"}
        </span>
        <span className="text-[11px] leading-4 tracking-[0.5px] font-[500] text-[#A3A3A3]">
          {t(I18nKey.GITHUB$TOKEN_LABEL)}
          <span className="text-[#A3A3A3]">
            {" "}
            {t(I18nKey.CUSTOM_INPUT$OPTIONAL_LABEL)}
          </span>
        </span>
        {isSet && (
          <Tooltip content="Unset GitHub token">
            <button
              data-testid="unset-github-token-button"
              type="button"
              aria-label="Unset GitHub token"
              onClick={onUnset}
              className="text-[#A3A3A3] hover:text-[#FF4D4F]"
            >
              <FaCircleXmark size={16} />
            </button>
          </Tooltip>
        )}
      </div>
      {!isSet && (
        <input
          data-testid="github-token-input"
          id="ghToken"
          name="ghToken"
          type="password"
          className="bg-[#27272A] text-xs py-[10px] px-3 rounded"
        />
      )}
    </label>
  );
}
