import ActionType from "#/types/action-type";

export function getTerminalCommand(command: string, hidden: boolean = false) {
  const event = { action: ActionType.RUN, args: { command, hidden } };
  return event;
}

export function getGitHubTokenCommand(gitHubToken: string) {
  const command = `export GITHUB_TOKEN=${gitHubToken}`;
  const event = getTerminalCommand(command, true);
  return event;
}
