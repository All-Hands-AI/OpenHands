import useDocusaurusContext from "@docusaurus/useDocusaurusContext";
import Layout from "@theme/Layout";
import { HomepageHeader } from "../components/HomepageHeader/HomepageHeader";
import { Welcome } from "../components/Welcome/Welcome";
import { translate } from '@docusaurus/Translate';

export function Header({ title, summary, description }): JSX.Element {
  return (
    <div>
      <h1>{title}</h1>
      <h2 style={{ fontSize: "40px" }}>{summary}</h2>
      <h3 className="headerDescription">{description}</h3>
    </div>
  );
}

export default function Home(): JSX.Element {
  const { siteConfig } = useDocusaurusContext();
  return (
    <>
    <Layout
      title={`${siteConfig.title}`}
      description={translate({
        id: 'homepage.description',
        message: 'AI-powered code generation for software engineering.',
        description: 'The homepage description',
      })}
    >
      <div>
        <HomepageHeader />
        <div>
          <Welcome />
        </div>
      </div>
    </Layout>
    </>
  );
}
