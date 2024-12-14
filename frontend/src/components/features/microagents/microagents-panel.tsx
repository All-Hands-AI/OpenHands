import React from "react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { Button } from "../../shared/buttons/button";

interface MicroagentsPanelProps {
  repoName: string;
  hasMicroagents: boolean;
  onAddTemporary: () => void;
  onAddPermanent: () => void;
}

export function MicroagentsPanel({
  repoName,
  hasMicroagents,
  onAddTemporary,
  onAddPermanent,
}: MicroagentsPanelProps) {
  const { t } = useTranslation();

  return (
    <div className="flex flex-col gap-4 p-4 bg-root-primary rounded-xl">
      <div className="flex items-center justify-between">
        <span className="text-xl leading-6 font-semibold -tracking-[0.01em]">
          {t(I18nKey.MICROAGENTS_PANEL$TITLE)}
        </span>
        <div className="flex gap-2">
          <Button
            type="button"
            variant="secondary"
            onClick={onAddTemporary}
            text={t(I18nKey.MICROAGENTS_PANEL$ADD_TEMPORARY_BUTTON)}
          />
          <Button
            type="button"
            variant="primary"
            onClick={onAddPermanent}
            text={t(I18nKey.MICROAGENTS_PANEL$ADD_PERMANENT_BUTTON)}
          />
        </div>
      </div>

      {hasMicroagents ? (
        <div className="flex flex-col gap-2">
          <p className="text-sm text-[#A3A3A3]">
            {t(I18nKey.MICROAGENTS_PANEL$AGENTS_FOUND, { repoName })}
          </p>
        </div>
      ) : (
        <p className="text-sm text-[#A3A3A3]">
          {t(I18nKey.MICROAGENTS_PANEL$NO_AGENTS, { repoName })}
        </p>
      )}
    </div>
  );
}
