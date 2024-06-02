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
            <div className="faq-section-title">General</div>
            <div>What is Devin?</div>
            <div>
              <span className="highlight">Devin</span>{" "}
              represents a cutting-edge autonomous agent designed to navigate the
              complexities of software engineering. It leverages a combination of
              tools such as a shell, code editor, and web browser, showcasing the
              untapped potential of LLMs in software development. Our goal is to
              explore and expand upon Devin's capabilities, identifying both its
              strengths and areas for improvement, to guide the progress of open
              code models.
            </div>
          </div>
          <div className="faq-section">
            <div className="faq-section-title">Why OpenDevin?</div>
            <p>
              The{" "}
              <span className="highlight">OpenDevin</span>{" "}
              project is born out of a desire to replicate, enhance, and innovate
              beyond the original Devin model. By engaging the{" "}
              <a href="https://github.com/OpenDevin/OpenDevin">
                open-source community
              </a>
              , we aim to tackle the challenges faced by Code LLMs in practical
              scenarios, producing works that significantly contribute to the
              community and pave the way for future advancements.
            </p>
          </div>
          <div className="faq-section">
            <div className="faq-section-title">How to fix an issue on OpenDevin?</div>
            <div className="faq-steps">
              To fix an issue on GitHub using OpenDevin, send a prompt to OpenDevin asking it to follow these steps:
              <ol>
                <li>Read the issue on <a href="https://github.com/OpenDevin/OpenDevin/issues/1611">GitHub</a></li>
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
        </div>
      </Layout>
    </>
  );
}
