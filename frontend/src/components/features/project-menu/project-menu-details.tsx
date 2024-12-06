import { useTranslation } from "react-i18next";
import ExternalLinkIcon from "#/icons/external-link.svg?react";
import { formatTimeDelta } from "#/utils/format-time-delta";
import { I18nKey } from "#/i18n/declaration";

interface ProjectMenuDetailsProps {
  repoName: string;
  avatar: string | null;
  lastCommit: GitHubCommit;
}

export function ProjectMenuDetails({
  repoName,
  avatar,
  lastCommit,
}: ProjectMenuDetailsProps) {
  const { t } = useTranslation();
  return (
    <div className="flex flex-col">
      <a
        href={`https://github.com/${repoName}`}
        target="_blank"
        rel="noreferrer noopener"
        className="flex items-center gap-2"
      >
        {avatar && <img src={avatar} alt="" className="w-4 h-4 rounded-full" />}
        <span className="text-sm leading-6 font-semibold">{repoName}</span>
        <ExternalLinkIcon width={16} height={16} />
      </a>
      <a
        href={lastCommit.html_url}
        target="_blank"
        rel="noreferrer noopener"
        className="text-xs text-[#A3A3A3] hover:underline hover:underline-offset-2"
      >
        <span>{lastCommit.sha.slice(-7)}</span> <span>&middot;</span>{" "}
        <span>
          {formatTimeDelta(new Date(lastCommit.commit.author.date))}{" "}
          {t(I18nKey.PROJECT_MENU_DETAILS$AGO_LABEL)}
        </span>
      </a>
    </div>
  );
}
