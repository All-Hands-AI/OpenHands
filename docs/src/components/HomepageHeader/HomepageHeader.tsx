import Link from "@docusaurus/Link";
import useDocusaurusContext from "@docusaurus/useDocusaurusContext";
import Heading from "@theme/Heading";
import { Demo } from "../Demo/Demo";
import styles from "./index.module.css";

export function HomepageHeader() {
  const { siteConfig } = useDocusaurusContext();
  return (
    <div className="h-screen bg-gradient-to-t from-slate-600 to-black">
    {/* <div className={styles.headerContainer}> */}
      <div className={`text-white flex flex-col 
      items-center p-6 font-light w-full`}>
        <Heading as="h1" className="
        text-5xl
        ">
          {/* hero__title  */}
          {siteConfig.title}
        </Heading>
        <p className="hero__subtitle">{siteConfig.tagline}</p>
        <div className={styles.buttons}>
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
