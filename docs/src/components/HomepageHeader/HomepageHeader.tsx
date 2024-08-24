import React from 'react';
import Link from "@docusaurus/Link";
import useDocusaurusContext from "@docusaurus/useDocusaurusContext";
import Heading from "@theme/Heading";
import { Demo } from "../Demo/Demo";
import Translate from '@docusaurus/Translate';
import "../../css/homepageHeader.css";

export function HomepageHeader() {
  const { siteConfig } = useDocusaurusContext();
  return (
    <div className="homepage-header">
      <div className="header-content">
        <Heading as="h1" className="header-title">
          {siteConfig.title}
        </Heading>

        <p className="header-subtitle">{siteConfig.tagline}</p>

        <div className="header-links">
          <a href="https://github.com/All-Hands-AI/OpenHands">
            <img src="https://img.shields.io/badge/Code-Github-purple?logo=github&logoColor=white&style=for-the-badge" alt="Code" />
          </a>
          <a href="https://join.slack.com/t/opendevin/shared_invite/zt-2oikve2hu-UDxHeo8nsE69y6T7yFX_BA">
            <img src="https://img.shields.io/badge/Slack-Join%20Us-red?logo=slack&logoColor=white&style=for-the-badge" alt="Join our Slack community" />
          </a>
          <a href="https://discord.gg/ESHStjSjD4">
            <img src="https://img.shields.io/badge/Discord-Join%20Us-purple?logo=discord&logoColor=white&style=for-the-badge" alt="Join our Discord community" />
          </a>

          <a href="https://arxiv.org/abs/2407.16741">
            <img src="https://img.shields.io/badge/Paper-%20on%20Arxiv-red?logo=arxiv&style=for-the-badge" alt="Paper on Arxiv" />
          </a>
          <a href="https://huggingface.co/spaces/OpenHands/evaluation">
            <img src="https://img.shields.io/badge/Evaluation-Benchmark%20on%20HF%20Space-green?logo=huggingface&style=for-the-badge" alt="Evaluation Benchmark" />
          </a>
        </div>

        <Demo />
      </div>
    </div>
  );
}
