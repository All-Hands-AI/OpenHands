import { useTranslation } from "react-i18next";
import { BaseModal } from "../../../shared/modals/base-modal/base-modal";
import { I18nKey } from "#/i18n/declaration";
import { CostSection } from "./cost-section";
import { UsageSection } from "./usage-section";
import { ContextWindowSection } from "./context-window-section";
import { EmptyState } from "./empty-state";
import useMetricsStore from "#/stores/metrics-store";

interface MetricsModalProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
}

export function MetricsModal({ isOpen, onOpenChange }: MetricsModalProps) {
  const { t } = useTranslation();
  const metrics = useMetricsStore();

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
              <CostSection
                cost={metrics?.cost ?? null}
                maxBudgetPerTask={metrics?.max_budget_per_task ?? null}
              />

              {metrics?.usage !== null && (
                <>
                  <UsageSection usage={metrics.usage} />
                  <ContextWindowSection
                    perTurnToken={metrics.usage.per_turn_token}
                    contextWindow={metrics.usage.context_window}
                  />
                </>
              )}
            </div>
          </div>
        )}

        {!metrics?.cost && !metrics?.usage && <EmptyState />}
      </div>
    </BaseModal>
  );
}
