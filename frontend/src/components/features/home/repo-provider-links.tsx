import { useConfig } from "#/hooks/query/use-config";

export function RepoProviderLinks() {
  const { data: config } = useConfig();

  const githubHref = config
    ? `https://github.com/apps/${config.APP_SLUG}/installations/new`
    : "";

  return (
    <div className="flex flex-col text-sm underline underline-offset-2 text-content-2 gap-4 w-fit">
      <a href={githubHref} target="_blank" rel="noopener noreferrer">
        Add GitHub repos
      </a>
    </div>
  );
}
