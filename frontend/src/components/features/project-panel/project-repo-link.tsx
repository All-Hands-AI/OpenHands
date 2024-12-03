interface ProjectRepoLinkProps {
  repo: string;
  onClick?: (event: React.MouseEvent<HTMLAnchorElement>) => void;
}

export function ProjectRepoLink({ repo, onClick }: ProjectRepoLinkProps) {
  return (
    <a
      data-testid="project-card-repo"
      href={`https://github.com/${repo}`}
      target="_blank noopener noreferrer"
      onClick={onClick}
      className="text-xs text-neutral-400 hover:text-neutral-200"
    >
      {repo}
    </a>
  );
}
