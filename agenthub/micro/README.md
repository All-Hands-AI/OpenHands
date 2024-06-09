## Introduction

This package contains definitions of micro-agents. A micro-agent is defined
in the following structure:

```
[AgentName]
├── agent.yaml
└── prompt.md
```

Note that `prompt.md` could use jinja2 template syntax. During runtime, `prompt.md`
is loaded and rendered, and used together with `agent.yaml` to initialize a
micro-agent.

Micro-agents can be used independently. You can also use `ManagerAgent` which knows
how to coordinate the agents and collaboratively finish a task.
