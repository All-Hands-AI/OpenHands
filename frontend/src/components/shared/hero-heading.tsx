import RocketImage from "#/assets/images/rocket-image";
// import { I18nKey } from "#/i18n/declaration"
import { useTranslation } from "react-i18next";

export function HeroHeading() {
  // const { t } = useTranslation()

  return (
    <div className="flex w-full max-w-[560px] flex-col items-center gap-4 text-center">
      <RocketImage />
      <h1 className="text-[38px] font-semibold leading-[32px] -tracking-[0.02em] text-neutral-100 dark:text-white">
        From curiosity to clarity!
      </h1>
      {/* <p className="mx-4 text-sm flex flex-col gap-2">
        <span className="text-neutral-700 dark:text-[#979995]">
          {t(I18nKey.LANDING$START_HELP)}{" "}
          <a
            rel="noopener noreferrer"
            target="_blank"
            href="https://docs.all-hands.dev/modules/usage/getting-started"
            className="text-neutral-700 dark:text-[#979995] underline underline-offset-[3px]"
          >
            {t(I18nKey.LANDING$START_HELP_LINK)}
          </a>
        </span>
      </p> */}
    </div>
  );
}
