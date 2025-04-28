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

        <div style={{
          textAlign: 'center',
          fontSize: '1.2rem',
          maxWidth: '800px',
          margin: '0 auto',
          padding: '0rem 0rem 1rem'
        }}>
        <p style={{ margin: '0' }}>
          <Translate>
            Use AI to tackle the toil in your backlog. Our agents have all the same tools as a human developer: they can modify code, run commands, browse the web,
            call APIs, and yes-even copy code snippets from StackOverflow.
          </Translate>
          <br/>
          <Link to="/modules/usage/installation"
            style={{
              textDecoration: 'underline',
              display: 'inline-block',
              marginTop: '0.5rem'
            }}
          >
            <Translate>Get started with OpenHands.</Translate>
          </Link>
        </p>
      </div>

        <div align="center" className="header-links">
          <a href="https://github.com/All-Hands-AI/OpenHands/graphs/contributors"><img src="https://img.shields.io/github/contributors/All-Hands-AI/OpenHands?style=for-the-badge&color=blue" alt="Contributors" /></a>
          <a href="https://github.com/All-Hands-AI/OpenHands/stargazers"><img src="https://img.shields.io/github/stars/All-Hands-AI/OpenHands?style=for-the-badge&color=blue" alt="Stargazers" /></a>
          <a href="https://codecov.io/github/All-Hands-AI/OpenHands?branch=main"><img alt="CodeCov" src="https://img.shields.io/codecov/c/github/All-Hands-AI/OpenHands?style=for-the-badge&color=blue" /></a>
          <a href="https://github.com/All-Hands-AI/OpenHands/blob/main/LICENSE"><img src="https://img.shields.io/github/license/All-Hands-AI/OpenHands?style=for-the-badge&color=blue" alt="MIT License" /></a>
          <br/>
          <a href="https://join.slack.com/t/openhands-ai/shared_invite/zt-2ngejmfw6-9gW4APWOC9XUp1n~SiQ6iw"><img src="https://img.shields.io/badge/Slack-Join%20Us-red?logo=slack&logoColor=white&style=for-the-badge" alt="Join our Slack community" /></a>
          <a href="https://discord.gg/ESHStjSjD4"><img src="https://img.shields.io/badge/Discord-Join%20Us-purple?logo=discord&logoColor=white&style=for-the-badge" alt="Join our Discord community" /></a>
          <a href="https://github.com/All-Hands-AI/OpenHands/blob/main/CREDITS.md"><img src="https://img.shields.io/badge/Project-Credits-blue?style=for-the-badge&color=FFE165&logo=github&logoColor=white" alt="Credits" /></a>
          <br/>
          <a href="https://arxiv.org/abs/2407.16741"><img src="https://img.shields.io/badge/Paper%20on%20Arxiv-000?logoColor=FFE165&logo=arxiv&style=for-the-badge" alt="Paper on Arxiv" /></a>
          <a href="https://huggingface.co/spaces/OpenHands/evaluation"><img src="https://img.shields.io/badge/Benchmark%20score-000?logoColor=FFE165&logo=huggingface&style=for-the-badge" alt="Evaluation Benchmark Score" /></a>
        </div>
      </div>
    </div>
  );
}
