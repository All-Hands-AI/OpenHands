"""
Action mapper for converting BrowserGym-style actions to Browser-Use actions.

This module provides functionality to parse BrowserGym action strings and convert them
to Browser-Use action models for execution.
"""

import re
from typing import Any, Dict, Union

from browser_use.controller.service import (
    ClickElementAction,
    GoToUrlAction,
    InputTextAction,
    ScrollAction,
    SearchGoogleAction,
    SendKeysAction,
    SwitchTabAction,
    CloseTabAction,
    UploadFileAction,
    DoneAction,
    NoParamsAction,
)


class ActionMapper:
    """Maps BrowserGym-style action strings to Browser-Use action models."""

    def __init__(self):
        # Compile regex patterns for action parsing
        self.goto_pattern = re.compile(r'goto\("([^"]+)"\)')
        self.click_pattern = re.compile(r'click\("([^"]+)"(?:,\s*button=\'([^\']+)\'(?:,\s*modifiers=\[([^\]]+)\])?)?\)')
        self.fill_pattern = re.compile(r'fill\("([^"]+)",\s*"([^"]*)"\)')
        self.scroll_pattern = re.compile(r'scroll\(([^,]+),\s*([^)]+)\)')
        self.search_pattern = re.compile(r'search_google\("([^"]+)"\)')
        self.send_keys_pattern = re.compile(r'send_keys\("([^"]+)",\s*"([^"]+)"\)')
        self.switch_tab_pattern = re.compile(r'switch_tab\(([^)]+)\)')
        self.close_tab_pattern = re.compile(r'close_tab\(\)')
        self.upload_file_pattern = re.compile(r'upload_file\("([^"]+)",\s*"([^"]+)"\)')
        self.noop_pattern = re.compile(r'noop(?:\(([^)]*)\))?')
        self.go_back_pattern = re.compile(r'go_back\(\)')
        self.go_forward_pattern = re.compile(r'go_forward\(\)')

    def parse_action(self, action_str: str) -> Union[Any, None]:
        """
        Parse a BrowserGym-style action string and return a Browser-Use action model.

        Args:
            action_str: BrowserGym action string (e.g., 'goto("https://example.com")')

        Returns:
            Browser-Use action model or None if parsing fails
        """
        action_str = action_str.strip()

        # Try to match each action pattern
        if match := self.goto_pattern.match(action_str):
            url = match.group(1)
            return GoToUrlAction(url=url, new_tab=False)

        elif match := self.click_pattern.match(action_str):
            bid = match.group(1)
            button = match.group(2) if match.group(2) else 'left'
            modifiers = match.group(3) if match.group(3) else None

            # Convert bid to index (this is a simplified mapping)
            # In a real implementation, you'd need to maintain a bid-to-index mapping
            index = self._bid_to_index(bid)
            return ClickElementAction(index=index)

        elif match := self.fill_pattern.match(action_str):
            bid = match.group(1)
            text = match.group(2)
            index = self._bid_to_index(bid)
            return InputTextAction(index=index, text=text)

        elif match := self.scroll_pattern.match(action_str):
            delta_x = float(match.group(1))
            delta_y = float(match.group(2))
            # Browser-Use scroll action uses 'down' boolean instead of direction
            return ScrollAction(down=delta_y > 0, num_pages=1)

        elif match := self.search_pattern.match(action_str):
            query = match.group(1)
            return SearchGoogleAction(query=query)

        elif match := self.send_keys_pattern.match(action_str):
            bid = match.group(1)
            keys = match.group(2)
            index = self._bid_to_index(bid)
            return SendKeysAction(index=index, keys=keys)

        elif match := self.switch_tab_pattern.match(action_str):
            tab_index = int(match.group(1))
            return SwitchTabAction(tab_index=tab_index)

        elif self.close_tab_pattern.match(action_str):
            return CloseTabAction()

        elif match := self.upload_file_pattern.match(action_str):
            bid = match.group(1)
            file_path = match.group(2)
            index = self._bid_to_index(bid)
            return UploadFileAction(index=index, file_path=file_path)

        elif match := self.noop_pattern.match(action_str):
            # noop action - could be used for waiting
            return NoParamsAction()

        elif self.go_back_pattern.match(action_str):
            # Browser-Use might have a different way to handle navigation
            # For now, we'll use a custom action or return None
            return None

        elif self.go_forward_pattern.match(action_str):
            # Browser-Use might have a different way to handle navigation
            # For now, we'll use a custom action or return None
            return None

        return None

    def _bid_to_index(self, bid: str) -> int:
        """
        Convert a BrowserGym bid (element identifier) to a Browser-Use index.

        This is a simplified implementation. In a real scenario, you'd need to:
        1. Maintain a mapping between bids and element indices
        2. Update this mapping when the page changes
        3. Handle cases where elements are not found

        Args:
            bid: BrowserGym element identifier

        Returns:
            Browser-Use element index
        """
        # For now, we'll use a simple hash-based approach
        # This is not ideal but provides a starting point
        try:
            # Try to convert bid to integer if it's numeric
            return int(bid)
        except ValueError:
            # If bid is not numeric, use hash
            return hash(bid) % 1000  # Modulo to keep reasonable range

    def get_supported_actions(self) -> list[str]:
        """Get list of supported BrowserGym action patterns."""
        return [
            'goto("url")',
            'click("bid")',
            'click("bid", button="left|middle|right", modifiers=["Shift", "Ctrl"])',
            'fill("bid", "text")',
            'scroll(delta_x, delta_y)',
            'search_google("query")',
            'send_keys("bid", "keys")',
            'switch_tab(tab_index)',
            'close_tab()',
            'upload_file("bid", "file_path")',
            'noop(wait_ms)',
            'go_back()',
            'go_forward()',
        ]
