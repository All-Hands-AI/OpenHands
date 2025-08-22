import { FaBitbucket, FaGithub, FaGitlab } from "react-icons/fa6";
import { Provider } from "#/types/settings";

interface GitProviderIconProps {
  gitProvider: Provider;
}

export function GitProviderIcon({ gitProvider }: GitProviderIconProps) {
  return (
    <>
      {gitProvider === "github" && <FaGithub size={14} />}
      {gitProvider === "gitlab" && <FaGitlab />}
      {gitProvider === "bitbucket" && <FaBitbucket />}
    </>
  );
}
