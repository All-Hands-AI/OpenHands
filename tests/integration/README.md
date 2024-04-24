In order to run integration tests, please ensure your workspace is empty.

Your `config.toml` should look like this:

```toml
LLM_MODEL="gpt-4-turbo"
LLM_API_KEY="<your-api-key>"
LLM_EMBEDDING_MODEL="openai"
WORKSPACE_MOUNT_PATH="<absolute-path-of-your-workspace>"
```

You can choose any model you'd like to generate the mock responses.
You can even handcraft mock responses, especially when you would like to test the behaviour of agent for corner cases. If you use a very weak model (e.g. 8B params), chance is most agents won't be able to finish the task.

```bash
# Remove logs iff you are okay to lose logs. This helps us locate the prompts and responses quickly, but is NOT a must.
rm -rf logs
# Clear the workspace, otherwise OpenDevin might not be able to reproduce your prompts in CI environment. Feel free to change the workspace name and path. Be sure to set `WORKSPACE_MOUNT_PATH` to the same absolute path.
rm -rf workspace
mkdir workspace
# Depending on the complexity of the task you want to test, you can change the number of iterations limit. Change agent accordingly. If you are adding a new test, try generating mock responses for every agent.
poetry run python ./opendevin/main.py -i 10 -t "Write a shell script 'hello.sh' that prints 'hello'." -c "MonologueAgent" -d "./workspace"
```

After running the above commands, you should be able to locate the real prompts
and responses logged. The log folder follows `logs/llm/%y-%m-%d_%H-%M` format.

Now, move all files under that folder to `tests/integration/mock/<AGENT>/<test-name>` folder. For example, moving all files from `logs/llm/24-04-23_21-55/` folder to
`tests/integration/mock/MonologueAgent/test_write_simple_script` folder.
