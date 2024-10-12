import pytest

from openhands.agenthub.browsing_agent.response_parser import (
    BrowseInteractiveAction,
    BrowsingResponseParser,
)


@pytest.mark.parametrize(
    'action_str, expected',
    [
        ("click('81'", "click('81')```"),
        (
            '"We need to search the internet\n```goto("google.com")',
            '"We need to search the internet\n```goto("google.com"))```',
        ),
        ("```click('81'", "```click('81')```"),
        ("click('81')", "click('81'))```"),
    ],
)
def test_parse_response(action_str: str, expected: str) -> None:
    # BrowsingResponseParser.parse_response
    parser = BrowsingResponseParser()
    response = {'choices': [{'message': {'content': action_str}}]}
    result = parser.parse_response(response)
    assert result == expected


@pytest.mark.parametrize(
    'action_str, expected_browser_actions, expected_thought, expected_msg_content',
    [
        ("click('81')```", "click('81')", '', ''),
        ("```click('81')```", "click('81')", '', ''),
        (
            "We need to perform a click\n```click('81')",
            "click('81')",
            'We need to perform a click',
            '',
        ),
    ],
)
def test_parse_action(
    action_str: str,
    expected_browser_actions: str,
    expected_thought: str,
    expected_msg_content: str,
) -> None:
    # BrowsingResponseParser.parse_action
    parser = BrowsingResponseParser()
    action = parser.parse_action(action_str)
    assert isinstance(action, BrowseInteractiveAction)
    assert action.browser_actions == expected_browser_actions
    assert action.thought == expected_thought
    assert action.browsergym_send_msg_to_user == expected_msg_content
