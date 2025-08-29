import React from "react";
import { useTranslation } from "react-i18next";
import { useSelector } from "react-redux";
import { BaseModal } from "../../shared/modals/base-modal/base-modal";
import { BudgetDisplay } from "../conversation-panel/budget-display";
import { RootState } from "#/store";
import { I18nKey } from "#/i18n/declaration";

interface MetricsModalProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
}

export function MetricsModal({ isOpen, onOpenChange }: MetricsModalProps) {
  const { t } = useTranslation();
  const metrics = useSelector((state: RootState) => state.metrics);

  return (
    <BaseModal
      isOpen={isOpen}
      onOpenChange={onOpenChange}
      title={t(I18nKey.CONVERSATION$METRICS_INFO)}
      testID="metrics-modal"
    >
      <div className="space-y-4">
        {(metrics?.cost !== null || metrics?.usage !== null) && (
          <div className="rounded-md p-3">
            <div className="grid gap-3">
              {metrics?.cost !== null && (
                <div className="flex justify-between items-center pb-2">
                  <span className="text-lg font-semibold">
                    {t(I18nKey.CONVERSATION$TOTAL_COST)}
                  </span>
                  <span className="font-semibold">
                    ${metrics.cost.toFixed(4)}
                  </span>
                </div>
              )}
              <BudgetDisplay
                cost={metrics?.cost ?? null}
                maxBudgetPerTask={metrics?.max_budget_per_task ?? null}
              />

              {metrics?.usage !== null && (
                <>
                  <div className="flex justify-between items-center pb-2">
                    <span>{t(I18nKey.CONVERSATION$INPUT)}</span>
                    <span className="font-semibold">
                      {metrics.usage.prompt_tokens.toLocaleString()}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-2 pl-4 text-sm">
                    <span className="text-neutral-400">
                      {t(I18nKey.CONVERSATION$CACHE_HIT)}
                    </span>
                    <span className="text-right">
                      {metrics.usage.cache_read_tokens.toLocaleString()}
                    </span>
                    <span className="text-neutral-400">
                      {t(I18nKey.CONVERSATION$CACHE_WRITE)}
                    </span>
                    <span className="text-right">
                      {metrics.usage.cache_write_tokens.toLocaleString()}
                    </span>
                  </div>

                  <div className="flex justify-between items-center border-b border-neutral-700 pb-2">
                    <span>{t(I18nKey.CONVERSATION$OUTPUT)}</span>
                    <span className="font-semibold">
                      {metrics.usage.completion_tokens.toLocaleString()}
                    </span>
                  </div>

                  <div className="flex justify-between items-center border-b border-neutral-700 pb-2">
                    <span className="font-semibold">
                      {t(I18nKey.CONVERSATION$TOTAL)}
                    </span>
                    <span className="font-bold">
                      {(
                        metrics.usage.prompt_tokens +
                        metrics.usage.completion_tokens
                      ).toLocaleString()}
                    </span>
                  </div>

                  <div className="flex flex-col gap-2">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold">
                        {t(I18nKey.CONVERSATION$CONTEXT_WINDOW)}
                      </span>
                    </div>
                    <div className="w-full h-1.5 bg-neutral-700 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-blue-500 transition-all duration-300"
                        style={{
                          width: `${Math.min(100, (metrics.usage.per_turn_token / metrics.usage.context_window) * 100)}%`,
                        }}
                      />
                    </div>
                    <div className="flex justify-end">
                      <span className="text-xs text-neutral-400">
                        {metrics.usage.per_turn_token.toLocaleString()} /{" "}
                        {metrics.usage.context_window.toLocaleString()} (
                        {(
                          (metrics.usage.per_turn_token /
                            metrics.usage.context_window) *
                          100
                        ).toFixed(2)}
                        % {t(I18nKey.CONVERSATION$USED)})
                      </span>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        )}

        {!metrics?.cost && !metrics?.usage && (
          <div className="rounded-md p-4 text-center">
            <p className="text-neutral-400">
              {t(I18nKey.CONVERSATION$NO_METRICS)}
            </p>
          </div>
        )}
      </div>
    </BaseModal>
  );
}
