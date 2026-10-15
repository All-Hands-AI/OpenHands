import { useTranslation } from "react-i18next";
import { BrandButton } from "#/components/features/settings/brand-button";
import { useRemoveWorktree } from "#/hooks/mutation/use-remove-worktree";
import { useWorktrees } from "#/hooks/query/use-worktrees";
import type { ConversationWorktree } from "#/api/worktrees-service";
import { I18nKey } from "#/i18n/declaration";
import { getApiErrorMessage } from "#/utils/api-error-message";
import {
  displayErrorToast,
  displaySuccessToast,
} from "#/utils/custom-toast-handlers";
import {
  formatRelativeTime,
  isInvalidTimestamp,
} from "#/utils/format-relative-time";
import {
  settingsListContainerClassName,
  settingsListDividerClassName,
  settingsListRowClassName,
} from "#/utils/settings-list-classes";
import { cn } from "#/utils/utils";

const SIZE_UNITS = [
  ["gigabyte", 1024 ** 3],
  ["megabyte", 1024 ** 2],
  ["kilobyte", 1024],
] as const;

function formatSize(bytes: number, locale: string): string {
  const [unit, size] =
    SIZE_UNITS.find(([, unitSize]) => bytes >= unitSize) ?? SIZE_UNITS[2];
  return new Intl.NumberFormat(locale, {
    style: "unit",
    unit,
    maximumFractionDigits: unit === "gigabyte" ? 1 : 0,
  }).format(bytes / size);
}

function WorktreeRow({ worktree }: { worktree: ConversationWorktree }) {
  const { t, i18n } = useTranslation("openhands");
  const { mutateAsync: removeWorktree, isPending } = useRemoveWorktree();
  const details = [
    worktree.repository?.split("/").pop(),
    formatSize(worktree.size_bytes, i18n.language),
    worktree.conversation_ids.length === 0
      ? t(I18nKey.SETTINGS$WORKTREES_LEFTOVER)
      : !isInvalidTimestamp(worktree.last_activity) &&
        formatRelativeTime(worktree.last_activity!, i18n.language, t),
  ].filter(Boolean);
  // Only a clean worktree no open conversation uses can go.
  const blocker = worktree.in_use
    ? t(I18nKey.SETTINGS$WORKTREES_IN_USE)
    : worktree.has_changes && t(I18nKey.SETTINGS$WORKTREES_HAS_CHANGES);

  return (
    <li
      className={cn(settingsListRowClassName, "h-auto gap-3 py-2")}
      data-testid={`worktree-${worktree.name}`}
    >
      <div className="flex min-w-0 flex-1 flex-col">
        <span className="truncate text-sm">
          {worktree.branch ?? worktree.name}
        </span>
        <span className="truncate text-xs text-muted">
          {details.join(" · ")}
        </span>
      </div>
      {blocker ? (
        <span className="shrink-0 text-xs text-muted">{blocker}</span>
      ) : (
        <BrandButton
          testId={`remove-worktree-${worktree.name}`}
          type="button"
          variant="secondary"
          isDisabled={isPending}
          onClick={async () => {
            // Awaited rather than mutate() callbacks: the refreshed list drops
            // this row, and React Query skips callbacks of an unmounted row.
            try {
              await removeWorktree(worktree.name);
              displaySuccessToast(t(I18nKey.SETTINGS$WORKTREES_REMOVED));
            } catch (error) {
              displayErrorToast(
                getApiErrorMessage(error, t(I18nKey.ERROR$GENERIC)),
              );
            }
          }}
        >
          {t(I18nKey.SETTINGS$WORKTREES_REMOVE)}
        </BrandButton>
      )}
    </li>
  );
}

/**
 * Worktrees on this machine, to free space. Removal keeps each branch, and
 * reopening a conversation brings its worktree back.
 */
export function WorktreeCleanup() {
  const { t } = useTranslation("openhands");
  const { data: worktrees } = useWorktrees();
  if (!worktrees?.length) return null;

  return (
    <section className="flex flex-col gap-2" data-testid="worktree-cleanup">
      <h3 className="text-sm font-medium">
        {t(I18nKey.SETTINGS$WORKTREES_TITLE)}
      </h3>
      <p className="text-xs text-muted">
        {t(I18nKey.SETTINGS$WORKTREES_DESCRIPTION)}
      </p>
      <ul
        className={cn(
          settingsListContainerClassName,
          settingsListDividerClassName,
        )}
      >
        {worktrees.map((worktree) => (
          <WorktreeRow key={worktree.name} worktree={worktree} />
        ))}
      </ul>
    </section>
  );
}
