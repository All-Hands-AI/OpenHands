import ActionType from "#/types/action-type";

export const generateDelegateToReadOnlyAction = () => ({
  action: ActionType.DELEGATE,
  args: {
    agent: "ReadOnlyAgent",
    inputs: {
      task: "Continue the conversation in READ-ONLY MODE. You can explore and analyze code but cannot make changes.",
    },
    thought: "Switching to read-only mode at user's request",
  },
});

export const generateFinishDelegationAction = () => ({
  action: ActionType.FINISH,
  args: {
    message:
      "Switching back to EXECUTE MODE. You now have full capabilities to modify code and execute commands.",
    task_completed: "true",
    outputs: {
      mode_switch: true,
    },
  },
});
