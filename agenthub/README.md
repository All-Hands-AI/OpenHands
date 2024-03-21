# Agent Framework Research

In this folder, there may exist multiple implementations of `Agent` that will be used by the 

For example, `agenthub/langchain_agent`, `agenthub/metagpt_agent`, `agenthub/codeact_agent`, etc.
Contributors from different backgrounds and interests can choose to contribute to any (or all!) of these directions.

## Constructing an Agent
Your agent must implement the following methods:

### `step`
```
def step(self, cmd_mgr: CommandManager) -> Event:
```
`step` moves the agent forward one step towards its goal. This probably means
sending a prompt to the LLM, then parsing the response into an action `Event`.

Each Event has an `action` and a dict of `args`. Supported Events include:
* `read` - reads the contents of a file. Arguments:
  * `path` - the path of the file to read
* `write` - writes the contents to a file. Arguments:
  * `path` - the path of the file to write
  * `contents` - the contents to write to the file
* `run` - runs a command. Arguments:
  * `command` - the command to run
  * `background` - if true, run the command in the background, so that other commands can be run concurrently. Useful for e.g. starting a server. You won't be able to see the logs. You don't need to end the command with `&`, just set this to true.
* `kill` - kills a background command
  * `id` - the ID of the background command to kill
* `browse` - opens a web page. Arguments:
  * `url` - the URL to open
* `recall` - recalls a past memory. Arguments:
  * `query` - the query to search for
* `think` - make a plan, set a goal, or record your thoughts. Arguments:
  * `thought` - the thought to record
* `finish` - if you're absolutely certain that you've completed your task and have tested your work, use the finish action to stop working.

For Events like `read` and `run`, a follow-up event will be added via `add_event` with the output.

### `add_event`
```
def add_event(self, event: Event) -> None:
```
`add_event` adds an event to the agent's history. This could be a user message,
an action taken by the agent, log output, file contents, or anything else.

You'll probably want to keep a history of events, and use them in your prompts
so that the agent knows what it did recently. You may also want to keep events
in a vector database so the agent can refer back to them.

The output of `step` will automatically be passed to this method.

### `search_memory`
```
def search_memory(self, query: str) -> List[str]:
```
`search_memory` should return a list of events that match the query. This will be used
for the `recall` action.
