import useDocusaurusContext from "@docusaurus/useDocusaurusContext";
import Layout from "@theme/Layout";

import { HomepageHeader } from "../components/HomepageHeader/HomepageHeader";
import { Welcome } from "../components/Welcome/Welcome";

export function Header({ title, summary, description }): JSX.Element {
  return (
    <div>
      <h2 style={{ fontSize: "40px" }}>{summary}</h2>
      <h3 className="headerDescription">{description}</h3>
    </div>
  );
}

export default function Home(): JSX.Element {
  const { siteConfig } = useDocusaurusContext();
  return (
    <Layout
      title={`Hello from ${siteConfig.title}`}
      description="AI-powered code generation for software engineering."
    >
      <div>
        <HomepageHeader />
        <div>
          <Welcome />
        </div>
      </div>
    </Layout>
  );
}
