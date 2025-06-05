# Common timeout message template that can be used across different timeout scenarios
TIMEOUT_MESSAGE_TEMPLATE = (
    "You may wait longer to see additional output by sending empty command '', "
    'send other commands to interact with the current process, '
    'send keys to interrupt/kill the command, '
    'or use {timeout_param} parameter in execute_bash {timeout_action} for future commands.'
)
