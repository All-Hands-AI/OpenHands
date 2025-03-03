import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import { HomepageHeader } from '../components/HomepageHeader/HomepageHeader';
import { translate } from '@docusaurus/Translate';
import { Demo } from "../components/Demo/Demo";

export default function Home(): JSX.Element {
  const { siteConfig } = useDocusaurusContext();
  return (
    <Layout
      title={`${siteConfig.title}`}
      description={translate({
        id: 'homepage.description',
        message: 'Code Less, Make More',
      })}
    >
      <HomepageHeader />

      <div style={{ textAlign: 'center', padding: '1rem 0' }}>
        <Demo />
      </div>

      <div style={{ textAlign: 'center', padding: '0.5rem 2rem 1.5rem' }}>
        <h2>Most Popular Links</h2>
        <ul style={{ listStyleType: 'none'}}>
          <li><a href="/modules/usage/prompting/microagents-repo">Customizing OpenHands to a repository</a></li>
          <li><a href="/modules/usage/how-to/github-action">Integrating OpenHands with Github</a></li>
          <li><a href="/modules/usage/llms#model-recommendations">Recommended models to use</a></li>
          <li><a href="/modules/usage/runtimes#connecting-to-your-filesystem">Connecting OpenHands to your filesystem</a></li>
        </ul>
      </div>
    </Layout>
  );
}
