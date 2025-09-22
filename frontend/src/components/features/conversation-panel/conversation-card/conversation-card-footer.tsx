import { useTranslation } from "react-i18next";
import { formatTimeDelta } from "#/utils/format-time-delta";
import { cn } from "#/utils/utils";
import { I18nKey } from "#/i18n/declaration";
import { RepositorySelection } from "#/api/open-hands.types";
import { ConversationRepoLink } from "./conversation-repo-link";
import { NoRepository } from "./no-repository";

interface ConversationCardFooterProps {
  selectedRepository: RepositorySelection | null;
  lastUpdatedAt: string; // ISO 8601
  createdAt?: string; // ISO 8601
}

export function ConversationCardFooter({
  selectedRepository,
  lastUpdatedAt,
  createdAt,
}: ConversationCardFooterProps) {
  const { t } = useTranslation();

  return (
    <div className={cn("flex flex-row justify-between items-center mt-1")}>
      {selectedRepository?.selected_repository ? (
        <ConversationRepoLink selectedRepository={selectedRepository} />
      ) : (
        <NoRepository />
      )}
      {(createdAt ?? lastUpdatedAt) && (
        <p className="text-xs text-[#A3A3A3] flex-1 text-right">
          <time>
            {`${formatTimeDelta(new Date(lastUpdatedAt ?? createdAt))} ${t(I18nKey.CONVERSATION$AGO)}`}
          </time>
        </p>
      )}
    </div>
  );
}
