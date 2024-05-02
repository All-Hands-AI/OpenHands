import Layout from "@theme/Layout";

export default function FAQ() {
  return (
    <Layout title="FAQ" description="Frequently Asked Questions">
      <div
        id="faq"
        style={{
          maxWidth: "900px",
          margin: "0px auto",
          padding: "40px",
          textAlign: "justify",
        }}
      >
        <h1 style={{ fontSize: "3rem" }}>Frequently Asked Questions</h1>
        <h2 style={{ fontSize: "2rem" }}>Support</h2>
        <h3>How can I report an issue with OpenDevin?</h3>
        <p>
          Please file a bug on{" "}
          <a href="https://github.com/OpenDevin/OpenDevin/issues">GitHub</a> if
          you notice a problem that likely affects others.
          If you're having trouble installing, or have general questions, reach out on{" "}
          <a href="https://discord.gg/mBuDGRzzES">Discord</a> or{" "}
          <a href="https://join.slack.com/t/opendevin/shared_invite/zt-2ggtwn3k5-PvAA2LUmqGHVZ~XzGq~ILw">Slack</a>.
        </p>
        <h2 style={{ fontSize: "2rem" }}>General</h2>
        <h3>What is Devin?</h3>
        <p>
          <span style={{ fontWeight: "600", color: "var(--logo)" }}>Devin</span>{" "}
          represents a cutting-edge autonomous agent designed to navigate the
          complexities of software engineering. It leverages a combination of
          tools such as a shell, code editor, and web browser, showcasing the
          untapped potential of LLMs in software development. Our goal is to
          explore and expand upon Devin's capabilities, identifying both its
          strengths and areas for improvement, to guide the progress of open
          code models.
        </p>
        <h3>Why OpenDevin?</h3>
        <p>
          The{" "}
          <span style={{ fontWeight: "600", color: "var(--logo)" }}>
            OpenDevin
          </span>{" "}
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
    </Layout>
  );
}
