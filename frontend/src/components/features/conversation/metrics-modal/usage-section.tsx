import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";

interface UsageSectionProps {
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
    cache_read_tokens: number;
    cache_write_tokens: number;
  };
}

export function UsageSection({ usage }: UsageSectionProps) {
  const { t } = useTranslation();

  return (
    <>
      <div className="flex justify-between items-center pb-2">
        <span>{t(I18nKey.CONVERSATION$INPUT)}</span>
        <span className="font-semibold">
          {usage.prompt_tokens.toLocaleString()}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-2 pl-4 text-sm">
        <span className="text-neutral-400">
          {t(I18nKey.CONVERSATION$CACHE_HIT)}
        </span>
        <span className="text-right">
          {usage.cache_read_tokens.toLocaleString()}
        </span>
        <span className="text-neutral-400">
          {t(I18nKey.CONVERSATION$CACHE_WRITE)}
        </span>
        <span className="text-right">
          {usage.cache_write_tokens.toLocaleString()}
        </span>
      </div>

      <div className="flex justify-between items-center border-b border-neutral-700 pb-2">
        <span>{t(I18nKey.CONVERSATION$OUTPUT)}</span>
        <span className="font-semibold">
          {usage.completion_tokens.toLocaleString()}
        </span>
      </div>

      <div className="flex justify-between items-center border-b border-neutral-700 pb-2">
        <span className="font-semibold">{t(I18nKey.CONVERSATION$TOTAL)}</span>
        <span className="font-bold">
          {(usage.prompt_tokens + usage.completion_tokens).toLocaleString()}
        </span>
      </div>
    </>
  );
}
