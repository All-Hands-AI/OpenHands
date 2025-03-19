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
        <h2><Translate>Most Popular Links</Translate></h2>
        <ul style={{ listStyleType: 'none'}}>
          <li>
            <Link to={`/${useDocusaurusContext().i18n.currentLocale}/usage/prompting/microagents-repo`}>
              <Translate>Customizing OpenHands to a repository</Translate>
            </Link>
          </li>
          <li>
            <Link to={`/${useDocusaurusContext().i18n.currentLocale}/usage/how-to/github-action`}>
              <Translate>Integrating OpenHands with Github</Translate>
            </Link>
          </li>
          <li>
            <Link to={`/${useDocusaurusContext().i18n.currentLocale}/usage/llms#model-recommendations`}>
              <Translate>Recommended models to use</Translate>
            </Link>
          </li>
          <li>
            <Link to={`/${useDocusaurusContext().i18n.currentLocale}/usage/runtimes#connecting-to-your-filesystem`}>
              <Translate>Connecting OpenHands to your filesystem</Translate>
            </Link>
          </li>
        </ul>
      </div>
    </Layout>
  );
}
