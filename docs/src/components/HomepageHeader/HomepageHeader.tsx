import Link from "@docusaurus/Link";
import useDocusaurusContext from "@docusaurus/useDocusaurusContext";
import Heading from "@theme/Heading";
import { Demo } from "../Demo/Demo";
import "../../css/homepageHeader.css"; // Importing the CSS file

export function HomepageHeader() {
  const { siteConfig } = useDocusaurusContext();
  return (
    <div className="homepage-header">
      <div className="header-content">
        <Heading as="h1" className="header-title">
          {siteConfig.title}
        </Heading>
        <p className="header-subtitle">{siteConfig.tagline}</p>
        <div className="header-buttons">
          <Link
            className="button button--secondary button--lg"
            to="/modules/usage/intro"
          >
            Get Started
          </Link>
        </div>
        <Demo />
      </div>
    </div>
  );
}

