export interface TaskItem {
  /**
   * A brief title for the task.
   */
  title: string;
  /**
   * Additional details or notes about the task.
   */
  notes: string;
  /**
   * The current status of the task. One of 'todo', 'in_progress', or 'done'.
   */
  status: "todo" | "in_progress" | "done";
}

export interface CmdOutputMetadata {
  /**
   * The exit code of the last executed command
   */
  exit_code: number;
  /**
   * The process ID of the last executed command
   */
  pid: number;
  /**
   * The username of the current user
   */
  username: string | null;
  /**
   * The hostname of the machine
   */
  hostname: string | null;
  /**
   * The current working directory
   */
  working_dir: string | null;
  /**
   * The path to the current Python interpreter, if any
   */
  py_interpreter_path: string | null;
  /**
   * Prefix to add to command output
   */
  prefix: string;
  /**
   * Suffix to add to command output
   */
  suffix: string;
}
