import Link from "@docusaurus/Link";
import { Header } from "@site/src/pages";
import { CodeBlock } from "./CodeBlock";
import styles from "./styles.module.css";

export function Code() {
  const keyCode = `# Your OpenAI API key, or any other LLM API key
export LLM_API_KEY="sk-..."`;

  const workspaceCode = `# The directory you want OpenDevin to modify. MUST be an absolute path!
export WORKSPACE_BASE=$(pwd)/workspace`;

  const dockerCode = `docker run \\
    -e LLM_API_KEY \\
    -e WORKSPACE_MOUNT_PATH=$WORKSPACE_BASE \\
    -v $WORKSPACE_BASE:/opt/workspace_base \\
    -v /var/run/docker.sock:/var/run/docker.sock \\
    -p 3000:3000 \\
    --add-host host.docker.internal=host-gateway \\
    ghcr.io/opendevin/opendevin:0.3.1`;

  return (
    <div className={styles.container}>
      <div className={styles.innerContainer}>
        <div className={styles.header}>
          <Header
            title="Getting Started"
            summary="Getting Started"
            description="Get started using OpenDevin in just a few lines of code"
          ></Header>
          <div className={styles.buttons}>
            <Link
              className="button button--secondary button--lg"
              to="/modules/usage/intro"
            >
              Learn More
            </Link>
          </div>
        </div>
        <br />
        <CodeBlock language="python" code={keyCode} />
        <CodeBlock language="python" code={workspaceCode} />
        <CodeBlock language="python" code={dockerCode} />
      </div>
    </div>
  );
}
