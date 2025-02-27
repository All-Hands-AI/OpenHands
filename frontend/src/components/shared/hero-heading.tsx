import { useTranslation } from "react-i18next";
import BuildIt from "#/icons/build-it.svg?react";
import { I18nKey } from "#/i18n/declaration";

export function HeroHeading() {
  const { t } = useTranslation();
  return (
    <div className="w-[304px] text-center flex flex-col gap-4 items-center py-4">
      <BuildIt width={88} height={104} />
      <h1 className="text-[38px] leading-[32px] -tracking-[0.02em]">
        {t(I18nKey.LANDING$TITLE)}
      </h1>
      <p className="mx-4 text-sm flex flex-col gap-2">
        {t(I18nKey.LANDING$SUBTITLE)}{" "}
        <span className="">
          {t(I18nKey.LANDING$START_HELP)}{" "}
          <a
            rel="noopener noreferrer"
            target="_blank"
            href="https://docs.all-hands.dev/modules/usage/getting-started"
            className="text-white underline underline-offset-[3px]"
          >
            {t(I18nKey.LANDING$START_HELP_LINK)}
          </a>
        </span>
      </p>
    </div>
  );
}
