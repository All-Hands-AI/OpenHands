import React from 'react';
import Layout from "@theme/Layout";
import "../css/faq.css";
import Translate, { translate } from '@docusaurus/Translate';

export default function FAQ() {
  return (
    <>
      <Layout
        title={translate({ id: 'faq.title', message: 'FAQ' })}
        description={translate({ id: 'faq.description', message: 'Frequently Asked Questions' })}
      >
        <div id="faq" className="faq-container">
          <div className="faq-title">
            <Translate id="faq.title">Frequently Asked Questions</Translate>
          </div>
          <div className="faq-section">
            <div className="faq-section-title">
              <Translate id="faq.support.title">Support</Translate>
            </div>
            <div>
              <Translate id="faq.support.issue">How can I report an issue with OpenDevin?</Translate>
            </div>
            <div>
              <Translate
                id="faq.support.report"
                values={{
                  githubLink: (
                    <a href="https://github.com/OpenDevin/OpenDevin/issues" target="_blank">GitHub</a>
                  ),
                  discordLink: (
                    <a href="https://discord.gg/mBuDGRzzES" target="_blank">Discord</a>
                  ),
                  slackLink: (
                    <a href="https://join.slack.com/t/opendevin/shared_invite/zt-2jsrl32uf-fTeeFjNyNYxqSZt5NPY3fA" target="_blank">Slack</a>
                  ),
                }}
              >
                {'Please file a bug on {githubLink} if you notice a problem that likely affects others. If you\'re having trouble installing, or have general questions, reach out on {discordLink} or {slackLink}.'}
              </Translate>
            </div>
          </div>
          <div className="faq-section">
            <div className="faq-section-title">
              <Translate id="faq.general.title">General</Translate>
            </div>
            <div>
              <Translate id="faq.general.what">What is Devin?</Translate>
            </div>
            <div>
              <Translate
                id="faq.general.devin"
                values={{ highlight: <span className="highlight">Devin</span> }}
              >
                {'{highlight} represents a cutting-edge autonomous agent designed to navigate the complexities of software engineering. It leverages a combination of tools such as a shell, code editor, and web browser, showcasing the untapped potential of LLMs in software development. Our goal is to explore and expand upon Devin\'s capabilities, identifying both its strengths and areas for improvement, to guide the progress of open code models.'}
              </Translate>
            </div>
          </div>
          <div className="faq-section">
            <div className="faq-section-title">
              <Translate id="faq.why.title">Why OpenDevin?</Translate>
            </div>
            <p>
              <Translate
                id="faq.why.opendevin"
                values={{
                  highlight: <span className="highlight">OpenDevin</span>,
                  githubLink: <a href="https://github.com/OpenDevin/OpenDevin">open-source community</a>,
                }}
              >
                {'The {highlight} project is born out of a desire to replicate, enhance, and innovate beyond the original Devin model. By engaging the {githubLink}, we aim to tackle the challenges faced by Code LLMs in practical scenarios, producing works that significantly contribute to the community and pave the way for future advancements.'}
              </Translate>
            </p>
          </div>
          <div className="faq-section">
            <div className="faq-section-title">
              <Translate id="faq.fix.title">How to fix an issue on OpenDevin?</Translate>
            </div>
            <div className="faq-steps">
              <Translate id="faq.fix.steps">
                {'To fix an issue on GitHub using OpenDevin, send a prompt to OpenDevin asking it to follow these steps:'}
              </Translate>
              <ol>
                <li>
                  <Translate
                    id="faq.fix.step1"
                    values={{ githubLink: <a href="https://github.com/OpenDevin/OpenDevin/issues/1611">GitHub</a> }}
                  >
                    {'Read the issue on {githubLink}'}
                  </Translate>
                </li>
                <li>
                  <Translate id="faq.fix.step2">Clone the repository and check out a new branch</Translate>
                </li>
                <li>
                  <Translate id="faq.fix.step3">Based on the instructions in the issue description, modify files to fix the issue</Translate>
                </li>
                <li>
                  <Translate id="faq.fix.step4">Push the resulting output to GitHub using the GITHUB_TOKEN environment variable</Translate>
                </li>
                <li>
                  <Translate id="faq.fix.step5">Tell me the link that I need to go to to send a pull request</Translate>
                </li>
              </ol>
              <Translate id="faq.fix.beforeRun">
                {'Before you run OpenDevin, you can do:'}
              </Translate>
              <div className="command-box">
                <Translate id="faq.fix.command1">export SANDBOX_ENV_GITHUB_TOKEN=XXX</Translate>
              </div>
              <Translate id="faq.fix.note1">
                {'where XXX is a GitHub token that you created that has permissions to push to the OpenDevin repo. If you don’t have write permission to the OpenDevin repo, you might need to change that to:'}
              </Translate>
              <div className="command-box">
                <Translate id="faq.fix.command2">
                  {'Push the resulting output to my fork at https://github.com/USERNAME/OpenDevin/ using the GITHUB_TOKEN environment variable'}
                </Translate>
              </div>
              <Translate id="faq.fix.note2">
                {'where USERNAME is your GitHub username.'}
              </Translate>
            </div>
          </div>
        </div>
      </Layout>
    </>
  );
}
