# OpenDevin

## Mission 🎯
Devin is an autonomous agent 🤖 that tackles software engineering tasks through the use of its shell, code editor, and web browser. This rekindles the immense potential of LLMs in the software engineering domain, offering a new beacon of hope. This project aspires to replicate, enhance, and innovate upon Devin through the power of the open-source community.

🐚 Code Less, Make More.

## What is OpenDevin?
OpenDevin is a multi-agent AI assistant that imitates a software engineer to execute software projects autonomously based on a text input.

**PMDevin:**

Converts user’s input into an FRD. Breaks down the FRD into multiple stories and creates PRs and assigns them to Engineer Devin.

**EngineerDevin:**

- Takes the FRD as input and converts it into a technical requirements doc: outlining the software architecture, decide on the tech stack and a high level summary on the technical decisions made.
- Picks up PRs and begins the development task with the core objective of successfully closing all open PRs.
- Creates the dev environment, pulls the repository and begins development.
- Follows a TDD pattern as a measure of completeness for each task. (What does done look like?)

**TesterDevin:**

- Runs the BDD framework triggered when all PRs are closed.
- Reopens PR that fails the test.
- Assigns it back to the Engineer.

**DelegatorDevin:**
The main point of contact between the user and the rest of the agents. Delegator interacts with the user and delegates the engineering tasks to the underlying agents. This ensures "multitasking" so as to address user interrupts and spawn multiple engineering tasks in their own isolated environments.
