import Layout from '@theme/Layout';
import '../css/faq.css';
import Translate, { translate } from '@docusaurus/Translate';

export default function FAQ() {
  const githubLink = (
    <a href="https://github.com/OpenDevin/OpenDevin/issues" target="_blank">GitHub</a>
  );
  const discordLink = (
    <a href="https://discord.gg/mBuDGRzzES" target="_blank">Discord</a>
  );
  const slackLink = (
    <a href="https://join.slack.com/t/opendevin/shared_invite/zt-2ngejmfw6-9gW4APWOC9XUp1n~SiQ6iw" target="_blank">Slack</a>
  );

  return (
    <Layout
      title={translate({ id: 'faq.title', message: 'FAQ' })}
      description={translate({ id: 'faq.description', message: 'Frequently Asked Questions' })}
    >
      <div id="faq" className="faq-container">
        <div className="faq-title">
          <Translate id="faq.title" description="FAQ Title">Frequently Asked Questions</Translate>
        </div>
        <div className="faq-section">
          <div className="faq-section-title">
            <Translate id="faq.section.title.1" description="First Section Title">What is OpenDevin?</Translate>
          </div>
          <p>
            <span className="highlight"><Translate id="faq.section.highlight" description="Highlight Text">OpenDevin</Translate></span>{" "}
            <Translate id="faq.section.description.1" description="Description for OpenDevin">
              is an autonomous software engineer that can solve software engineering
              and web-browsing tasks end-to-end. It can perform data science queries, such
              as "Find the number of pull requests to the OpenDevin repository in the last
              month," and software engineering tasks, such as "Please add tests to this
              file and verify that all the tests pass. If they don't fix the file."
            </Translate>
          </p>
          <p>
            <Translate id="faq.section.description.2" description="Further Description for OpenDevin">
              At the same time, OpenDevin is a platform and community for agent developers
              to test out and evaluate new agents.
            </Translate>
          </p>
        </div>
        <div className="faq-section">
          <div className="faq-section-title">
            <Translate id="faq.section.title.2" description="Support Section Title">Support</Translate>
          </div>
          <div>
            <Translate
              id="faq.section.support.answer"
              description="Support Answer"
              values={{
                githubLink: githubLink,
                discordLink: discordLink,
                slackLink: slackLink,
              }}
            >
              {`Please file a bug on {githubLink} if you notice a problem that likely affects others. If you're having trouble installing, or have general questions, reach out on {discordLink} or {slackLink}.`}
            </Translate>
          </div>
        </div>
        <div className="faq-section">
          <div className="faq-section-title">
            <Translate id="faq.section.title.3" description="GitHub Issue Section Title">How to fix a GitHub issue with OpenDevin?</Translate>
          </div>
          <div className="faq-steps">
            <Translate id="faq.section.github.steps.intro" description="GitHub Steps Introduction">
              To fix an issue on GitHub using OpenDevin, send a prompt to OpenDevin asking it to follow
              steps like the following:
            </Translate>
            <ol>
              <li><Translate id="faq.section.github.step1" description="GitHub Step 1">Read the issue https://github.com/OpenDevin/OpenDevin/issues/1611</Translate></li>
              <li><Translate id="faq.section.github.step2" description="GitHub Step 2">Clone the repository and check out a new branch</Translate></li>
              <li><Translate id="faq.section.github.step3" description="GitHub Step 3">Based on the instructions in the issue description, modify files to fix the issue</Translate></li>
              <li><Translate id="faq.section.github.step4" description="GitHub Step 4">Push the resulting output to GitHub using the GITHUB_TOKEN environment variable</Translate></li>
              <li><Translate id="faq.section.github.step5" description="GitHub Step 5">Tell me the link that I need to go to to send a pull request</Translate></li>
            </ol>
            <Translate id="faq.section.github.steps.preRun" description="GitHub Steps Pre-Run">
              Before you run OpenDevin, you can do:
            </Translate>
            <div className="command-box">
              export SANDBOX_ENV_GITHUB_TOKEN=XXX
            </div>
            <Translate id="faq.section.github.steps.tokenInfo" description="GitHub Steps Token Info">
              where XXX is a GitHub token that you created that has permissions to push to the OpenDevin repo. If you don’t have write permission to the OpenDevin repo, you might need to change that to:
            </Translate>
            <div className="command-box">
              Push the resulting output to my fork at https://github.com/USERNAME/OpenDevin/ using the GITHUB_TOKEN environment variable
            </div>
            <Translate id="faq.section.github.steps.usernameInfo" description="GitHub Steps Username Info">
              where USERNAME is your GitHub username.
            </Translate>
          </div>
        </div>
        <div className="faq-section">
          <div className="faq-section-title">
            <Translate id="faq.section.title.4" description="Devin Section Title">How is OpenDevin different from Devin?</Translate>
          </div>
          <p>
            <a href="https://www.cognition.ai/blog/introducing-devin"><Translate id="faq.section.devin.linkText" description="Devin Link Text">Devin</Translate></a>&nbsp;
            <Translate id="faq.section.devin.description" description="Devin Description">
              is a commercial product by Cognition Inc., that served as the initial
              inspiration for OpenDevin. They both aim to do a good job at solving software
              engineering tasks, but OpenDevin you can download, use, and modify, while Devin
              you can only use through the Cognition site. In addition, OpenDevin has evolved
              beyond the initial inspiration, and now serves as a community-driven ecosystem for
              agent development in general, and we'd love to have you join and
            </Translate>
            <a href="https://github.com/OpenDevin/OpenDevin/blob/main/CONTRIBUTING.md"><Translate id="faq.section.devin.contribute" description="Contribute Link">contribute</Translate></a>!
          </p>
        </div>
        <div className="faq-section">
          <div className="faq-section-title">
            <Translate id="faq.section.title.5" description="ChatGPT Section Title">How is OpenDevin different from ChatGPT?</Translate>
          </div>
          <p>
            <Translate id="faq.section.chatgpt.description" description="ChatGPT Description">
              ChatGPT you can access online, it does not interface with local files, and
              its ability to execute code is limited. So it can write code, but it is not
              easy to test or execute it.
            </Translate>
          </p>
        </div>
      </div>
    </Layout>
  );
}
