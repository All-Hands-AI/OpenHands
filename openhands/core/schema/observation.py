from enum import Enum


class ObservationType(str, Enum):
    READ = 'read'
    """The content of a file
    """

    WRITE = 'write'

    EDIT = 'edit'

    BROWSE = 'browse'
    """The HTML content of a URL
    """

    RUN = 'run'
    """The output of a command
    """

    RUN_IPYTHON = 'run_ipython'
    """Runs a IPython cell.
    """

    CHAT = 'chat'
    """A message from the user
    """

    DELEGATE = 'delegate'
    """The result of a task delegated to another agent
    """

    MESSAGE = 'message'

    ERROR = 'error'

    SUCCESS = 'success'

    NULL = 'null'

    THINK = 'think'

    AGENT_STATE_CHANGED = 'agent_state_changed'

    USER_REJECTED = 'user_rejected'

    CONDENSE = 'condense'
    """Result of a condensation operation."""

    RECALL = 'recall'
    """Result of a recall operation. This can be the workspace context, a microagent, or other types of information."""

    MCP = 'mcp'
    """Result of a MCP Server operation"""

    BROWSER_MCP = 'browser_mcp'

    MCP_PLAN = 'mcp_plan'
    """Result of a MCP Plan operation. The response is a dict with the plan ID and the tasks."""

    PLAYWRIGHT_MCP_BROWSER_SCREENSHOT = 'playwright_mcp_browser_screenshot'
    """Result of a Playwright MCP Browser Screenshot operation. The response is a base64 encoded string of the screenshot, which should be streamed to the client using the correct format matching
    browsergym's screenshot format."""

    A2A_LIST_REMOTE_AGENTS = 'a2a_list_remote_agents'
    """Result of a A2A List Remote Agents operation. The response is a list of remote agents."""

    A2A_SEND_TASK_UPDATE_EVENT = 'a2a_send_task_update_event'
    """Result of a A2A Send Task Update Event operation. The response is a list of remote agents."""

    A2A_SEND_TASK_ARTIFACT = 'a2a_send_task_artifact'
    """Result of a A2A Send Task Artifact operation. The response is a list of remote agents."""

    A2A_SEND_TASK_RESPONSE = 'a2a_send_task_response'
    """Result of a A2A Send Task Response operation. The response is a list of remote agents."""

    REPORT_VERIFICATION = 'report_verification'
    """Result of the evaluation pipeline verifying the generated report. The response is a boolean."""
