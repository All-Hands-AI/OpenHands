## Introduction

CommitWriterAgent can help write git commit message. Example:

```bash
WORKSPACE_MOUNT_PATH="`PWD`" SANDBOX_TYPE="exec" \
  poetry run python opendevin/core/main.py -t "dummy task" -c CommitWriterAgent -d ./
```

This agent is special in the sense that it doesn't need a task. Once called,
it attempts to read all diff in the git staging area and write a good commit
message.

## Future work

### Feedback loop

The commit message could be (optionally) shown to the customer or
other agents, so that CommitWriterAgent could gather feedback to further
improve the commit message.

### Task rejection

When the agent cannot compile a commit message (e.g. not git repository), it
should reject the task with an explanation.
