import ExternalLinkIcon from "#/assets/external-link.svg?react";
import { formatTimeDelta } from "#/utils/format-time-delta";

interface ProjectMenuDetailsProps {
  repoName: string;
  avatar: string;
  lastCommit: GitHubCommit;
}

export function ProjectMenuDetails({
  repoName,
  avatar,
  lastCommit,
}: ProjectMenuDetailsProps) {
  return (
    <div className="flex flex-col">
      <a
        href={`https://github.com/${repoName}`}
        target="_blank"
        rel="noreferrer noopener"
        className="flex items-center gap-2"
      >
        <img src={avatar} alt="" className="w-4 h-4 rounded-full" />
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
          {formatTimeDelta(new Date(lastCommit.commit.author.date))} ago
        </span>
      </a>
    </div>
  );
}
