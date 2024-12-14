import React from "react";
import { useTranslation } from "react-i18next";
import ExternalLinkIcon from "#/icons/external-link.svg?react";
import { I18nKey } from "#/i18n/declaration";

interface InstructionsPanelProps {
  repoName: string;
  hasInstructions: boolean;
  tutorialUrl?: string;
  onAddInstructions: () => void;
}

export function InstructionsPanel({
  repoName,
  hasInstructions,
  tutorialUrl,
  onAddInstructions,
}: InstructionsPanelProps) {
  const { t } = useTranslation();

  return (
    <div className="flex flex-col gap-4 p-4 bg-root-primary rounded-xl">
      <div className="flex items-center justify-between">
        <span className="text-xl leading-6 font-semibold -tracking-[0.01em]">
          {t(I18nKey.INSTRUCTIONS_PANEL$TITLE)}
        </span>
        <button
          type="button"
          onClick={onAddInstructions}
          className="text-sm text-primary hover:opacity-80 font-medium"
        >
          {t(I18nKey.INSTRUCTIONS_PANEL$ADD_BUTTON)}
        </button>
      </div>

      {hasInstructions ? (
        <div className="flex flex-col gap-2">
          <p className="text-sm text-[#A3A3A3]">
            {t(I18nKey.INSTRUCTIONS_PANEL$INSTRUCTIONS_FOUND, { repoName })}
          </p>
          {tutorialUrl && (
            <a
              href={tutorialUrl}
              target="_blank"
              rel="noreferrer noopener"
              className="flex items-center gap-2 text-sm text-primary hover:opacity-80"
            >
              <span>{t(I18nKey.INSTRUCTIONS_PANEL$VIEW_TUTORIAL)}</span>
              <ExternalLinkIcon width={16} height={16} />
            </a>
          )}
        </div>
      ) : (
        <p className="text-sm text-[#A3A3A3]">
          {t(I18nKey.INSTRUCTIONS_PANEL$NO_INSTRUCTIONS, { repoName })}
        </p>
      )}
    </div>
  );
}
