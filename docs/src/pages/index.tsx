import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import { HomepageHeader } from '../components/HomepageHeader/HomepageHeader';
import { translate } from '@docusaurus/Translate';

export function Header({ title, summary }): JSX.Element {
  return (
    <div>
      <h1>{title}</h1>
      <h2 style={{ fontSize: '3rem' }}>{summary}</h2>
    </div>
  );
}

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
      <div style={{ textAlign: 'center', padding: '2rem' }}>
        <br />
        <h2>Most Popular Links</h2>
        <ul style={{ listStyleType: 'none'}}>
          <li><a href="/modules/usage/Installation">How to Run OpenHands</a></li>
          <li><a href="/modules/usage/prompting/microagents-repo">Customizing OpenHands to a repository</a></li>
          <li><a href="/modules/usage/how-to/github-action">Integrating OpenHands with Github</a></li>
          <li><a href="/modules/usage/llms#model-recommendations">Recommended models to use</a></li>
          <li><a href="/modules/usage/runtimes#connecting-to-your-filesystem">Connecting OpenHands to your filesystem</a></li>
        </ul>
      </div>
    </Layout>
  );
}
