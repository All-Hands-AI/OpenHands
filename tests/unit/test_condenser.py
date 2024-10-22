import argparse
import json
import os
from datetime import datetime
from pathlib import Path

from openhands.core import logger
from openhands.core.config.utils import get_llm_config_arg, load_app_config
from openhands.core.message import Message, TextContent
from openhands.events.action.agent import AgentSummarizeAction
from openhands.llm.llm import LLM
from openhands.memory.condenser import MemoryCondenser
from openhands.utils.prompt import PromptManager


def save_messages_for_debugging(
    messages: list[Message], summary_action: AgentSummarizeAction
) -> None:
    """
    Serializes the list of Message objects and the summary action,
    then saves them to a JSON file in the ./logs directory for debugging purposes.

    Args:
        messages (list[Message]): The list of messages to serialize.
        summary_action (AgentSummarizeAction): The summary action to append.
    """
    # Ensure the logs directory exists
    log_dir = Path('./logs')
    log_dir.mkdir(parents=True, exist_ok=True)

    # Generate a timestamped filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'debug_summary_{timestamp}.json'
    file_path = log_dir / filename

    try:
        # Serialize messages using Pydantic's model_dump()
        serialized_messages = [message.model_dump() for message in messages]

        # Create a Message instance for the summary_action
        summary_event = Message(
            role='assistant', content=[TextContent(text=str(summary_action))]
        )
        serialized_summary = summary_event.model_dump()

        # Append the serialized summary to the messages
        serialized_messages.append(serialized_summary)

        with file_path.open('w', encoding='utf-8') as f:
            json.dump(serialized_messages, f, ensure_ascii=False, indent=4)

        logger.debug(f'Messages successfully saved to {file_path}')
    except Exception as e:
        logger.error(f'Failed to save messages for debugging: {e}')


def main(condenser: MemoryCondenser, file_path: str | None = None):
    """
    Main method for quick testing and debugging.
    Reads a specified debug summary JSON file from the ./logs/deepseek-24sept directory,
    deserializes the messages, and prints them.
    If no file is specified, it falls back to the latest file based on timestamp.

    Args:
        file_path (str | None): The path to the log file to process. If None, the latest file is used.
    """
    log_dir = Path('./logs/deepseek-24sept')
    log_dir.mkdir(parents=True, exist_ok=True)

    if file_path:
        target_log = Path(file_path)
        if not target_log.exists():
            print(f'Specified log file does not exist: {target_log}')
            return
    else:
        log_files = list(log_dir.glob('instance_*_*.json'))

        if not log_files:
            print(
                'No instance_*_*.json files found in the ./logs/deepseek-24sept directory.'
            )
            return

        # Sort files to find the latest one based on the digits at the end of the filename
        def extract_digits(file_path: Path) -> int:
            try:
                # Extract the digits part from the filename
                digits_str = file_path.stem.split('_')[-1]
                return int(digits_str)
            except (IndexError, ValueError):
                # If digit extraction fails, assign the lowest possible value
                return -1

        log_files.sort(key=extract_digits, reverse=True)
        target_log = log_files[0]

        print(f'Loading messages from: {target_log}')

    try:
        with target_log.open('r', encoding='utf-8') as f:
            messages_data = json.load(f)

            # Deserialize messages using Pydantic's parse_obj
            messages: list[Message] = [
                Message.parse_obj(msg_dict) for msg_dict in messages_data
            ]

            print(f'Successfully loaded {len(messages)} messages:')
            # for msg in messages:
            #    print(f'{msg.role}:\n {msg.content[50:]}')
    except Exception as e:
        print(f'An error occurred while reading {target_log}: {e}')

    # run them through hell
    summary_action = condenser.condense(messages)
    print(f'summary_action: {summary_action}')


if __name__ == '__main__':
    # load or simulate dependencies as needed for testing
    app_config = load_app_config()
    llm_config = get_llm_config_arg('deepseek')
    if llm_config is not None:
        llm = LLM(config=llm_config)
    else:
        llm = LLM(app_config.get_llm_config('llm'))

    prompt_manager = PromptManager(
        prompt_dir=os.path.join(
            os.path.dirname(__file__), '..', 'agenthub', 'memcodeact_agent', 'prompts'
        ),
        agent_skills_docs='',
    )
    condenser = MemoryCondenser(llm=llm, prompt_manager=prompt_manager)

    # attach on fly the save_messages_for_debugging method to the condenser
    condenser.save_messages_for_debugging = save_messages_for_debugging

    # Setup argument parser for optional file parameter
    parser = argparse.ArgumentParser(description='Run MemoryCondenser on a .json file.')
    parser.add_argument(
        '--file',
        type=str,
        default=None,
        help='Path to the specific file to process. If not provided, the latest file is used.',
    )
    args = parser.parse_args()

    if args.file is not None and args.file == '':
        args.file = None

    # Call the main method with the specified file path if provided
    main(condenser, file_path=args.file)
