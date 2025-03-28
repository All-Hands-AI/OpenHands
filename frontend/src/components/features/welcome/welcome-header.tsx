import React from "react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import HandsIcon from "#/icons/build-it.svg?react";

export function WelcomeHeader() {
  const { t } = useTranslation();

  return (
    <div className="flex flex-col items-center gap-4 mb-8">
      <div className="flex justify-center">
        <HandsIcon width={88} height={88} />
      </div>
      <h1 className="text-3xl font-bold">{t(I18nKey.LANDING$TITLE)}</h1>
      <p className="text-center text-sm max-w-md">
        OpenHands makes it easy to build and maintain software using AI-driven
        development.
      </p>
      <div className="flex items-center gap-2 mt-2">
        <span className="text-sm text-gray-400">Not sure how to start?</span>
        <a
          href="https://docs.all-hands.dev/modules/usage/getting-started"
          target="_blank"
          rel="noopener noreferrer"
          className="text-sm text-white underline"
        >
          Read this
        </a>
      </div>
    </div>
  );
}
