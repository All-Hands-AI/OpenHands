import Layout from "@theme/Layout";
import CustomFooter from "../components/CustomFooter";
import "../css/faq.css";

export default function FAQ() {
  return (
    <>
      <Layout title="FAQ" description="Frequently Asked Questions">
        <div id="faq" className="faq-container">
          <div className="faq-title">Frequently Asked Questions</div>
          <div className="faq-section">
            <div className="faq-section-title">What is OpenDevin?</div>
            <p>
              <span className="highlight">OpenDevin</span>{" "}
              is an autonomous software engineer that can solve software engineering
              and web-browsing tasks end-to-end. It can perform data science queries, such
              as "Find the number of pull requests to the OpenDevin repository in the last
              month," and software engineering tasks, such as "Please add tests to this
              file and verify that all the tests pass. If they don't fix the file."
            </p>
            <p>
              At the same time, OpenDevin is a platform and community for agent developers
              to test out and evaluate new agents.
            </p>
          </div>
          <div className="faq-section">
            <div className="faq-section-title">Support</div>
            <div>How can I report an issue with OpenDevin?</div>
            <div>
              Please file a bug on{" "}
              <a href="https://github.com/OpenDevin/OpenDevin/issues" target="_blank">GitHub</a> if
              you notice a problem that likely affects others.
              If you're having trouble installing, or have general questions, reach out on{" "}
              <a href="https://discord.gg/mBuDGRzzES" target="_blank">Discord</a> or{" "}
              <a href="https://join.slack.com/t/opendevin/shared_invite/zt-2jsrl32uf-fTeeFjNyNYxqSZt5NPY3fA" target="_blank">Slack</a>.
            </div>
          </div>
          <div className="faq-section">
            <div className="faq-section-title">How to fix a GitHub issue with OpenDevin?</div>
            <div className="faq-steps">
              To fix an issue on GitHub using OpenDevin, send a prompt to OpenDevin asking it to follow
              steps like the following:
              <ol>
                <li>Read the issue https://github.com/OpenDevin/OpenDevin/issues/1611</li>
                <li>Clone the repository and check out a new branch</li>
                <li>Based on the instructions in the issue description, modify files to fix the issue</li>
                <li>Push the resulting output to GitHub using the GITHUB_TOKEN environment variable</li>
                <li>Tell me the link that I need to go to to send a pull request</li>
              </ol>
              Before you run OpenDevin, you can do:
              <div className="command-box">
                export SANDBOX_ENV_GITHUB_TOKEN=XXX
              </div>
              where XXX is a GitHub token that you created that has permissions to push to the OpenDevin repo. If you don’t have write permission to the OpenDevin repo, you might need to change that to:
              <div className="command-box">
                Push the resulting output to my fork at https://github.com/USERNAME/OpenDevin/ using the GITHUB_TOKEN environment variable
              </div>
              where USERNAME is your GitHub username.
            </div>
          </div>
          <div className="faq-section">
            <div className="faq-section-title">How is OpenDevin different from Devin?</div>
            <p>
              <a href="https://www.cognition.ai/blog/introducing-devin">Devin</a>&nbsp;
              is a commercial product by Cognition Inc., that served as the initial
              inspiration for OpenDevin. They both aim to do a good job at solving software
              engineering tasks, but OpenDevin you can download, use, and modify, while Devin
              you can only use through the Cognition site. In addition, OpenDevin has evolved
              beyond the initial inspiration, and now serves as a community-driven ecosystem for
              agent development in general, and we'd love to have you join and
              <a href="https://github.com/OpenDevin/OpenDevin/blob/main/CONTRIBUTING.md">contribute</a>!
            </p>
          </div>
          <div className="faq-section">
            <div className="faq-section-title">How is OpenDevin different from ChatGPT?</div>
            <p>
              ChatGPT you can access online, it does not interface with local files, and
              its ability to execute code is limited. So it can write code, but it is not
              easy to test or execute it.
            </p>
          </div>
        </div>
      </Layout>
    </>
  );
}
