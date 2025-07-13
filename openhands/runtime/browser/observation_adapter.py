"""
Observation adapter for converting Browser-Use observations to OpenHands format.

This module provides functionality to convert Browser-Use browser state information
into the OpenHands BrowserOutputObservation format for compatibility.
"""

import base64
import html2text
from typing import Any, Dict, Optional

from browser_use import BrowserSession
from openhands.events.observation import BrowserOutputObservation
from openhands.runtime.browser.base64 import image_to_png_base64_url


class ObservationAdapter:
    """Adapts Browser-Use observations to OpenHands BrowserOutputObservation format."""

    def __init__(self):
        self.html_text_converter = self._get_html_text_converter()

    def _get_html_text_converter(self) -> html2text.HTML2Text:
        """Get HTML to text converter with appropriate settings."""
        html_text_converter = html2text.HTML2Text()
        # ignore links and images
        html_text_converter.ignore_links = False
        html_text_converter.ignore_images = True
        # use alt text for images
        html_text_converter.images_to_alt = True
        # disable auto text wrapping
        html_text_converter.body_width = 0
        return html_text_converter

    async def create_observation(
        self,
        browser_session: BrowserSession,
        action_str: str,
        error: Optional[str] = None,
        return_axtree: bool = True,
    ) -> BrowserOutputObservation:
        """
        Create a BrowserOutputObservation from Browser-Use browser session.

        Args:
            browser_session: Browser-Use browser session
            action_str: The action string that was executed
            error: Error message if action failed
            return_axtree: Whether to include accessibility tree data

        Returns:
            BrowserOutputObservation in OpenHands format
        """
        try:
            # Get current page information
            current_page = browser_session.get_current_page()
            if not current_page:
                raise ValueError("No current page available")

            # Get page URL
            url = current_page.url if hasattr(current_page, 'url') else ''

            # Take screenshot
            screenshot = await self._get_screenshot(browser_session)

            # Get page HTML and convert to text
            html_content = await self._get_page_html(browser_session)
            text_content = self.html_text_converter.handle(html_content) if html_content else ''

            # Get page structure (DOM-like information)
            page_structure = await self._get_page_structure(browser_session)

            # Get tabs information
            tabs_info = browser_session.get_tabs_info()
            open_pages_urls = [tab.get('url', '') for tab in tabs_info] if tabs_info else []
            active_page_index = 0  # Browser-Use might have different tab management

            # Create observation
            observation = BrowserOutputObservation(
                content=text_content,
                url=url,
                screenshot=screenshot,
                screenshot_path=None,  # Will be set by calling code if needed
                set_of_marks='',  # Browser-Use doesn't provide this
                goal_image_urls=[],  # Evaluation-specific
                open_pages_urls=open_pages_urls,
                active_page_index=active_page_index,
                dom_object=page_structure.get('dom', {}) if return_axtree else {},
                axtree_object=page_structure.get('axtree', {}) if return_axtree else {},
                extra_element_properties=page_structure.get('properties', {}) if return_axtree else {},
                focused_element_bid='',  # Browser-Use might not provide this
                last_browser_action=action_str,
                last_browser_action_error=error or '',
                error=bool(error),
                trigger_by_action='browse_interactive',  # Default action type
            )

            return observation

        except Exception as e:
            # Create error observation
            return BrowserOutputObservation(
                content=str(e),
                url='',
                screenshot='',
                screenshot_path=None,
                error=True,
                last_browser_action_error=str(e),
                last_browser_action=action_str,
                trigger_by_action='browse_interactive',
            )

    async def _get_screenshot(self, browser_session: BrowserSession) -> str:
        """Get screenshot from browser session as base64 string."""
        try:
            screenshot_data = browser_session.take_screenshot()
            if screenshot_data:
                # Convert to base64 if needed
                if isinstance(screenshot_data, bytes):
                    return f"data:image/png;base64,{base64.b64encode(screenshot_data).decode()}"
                elif isinstance(screenshot_data, str):
                    if screenshot_data.startswith('data:image'):
                        return screenshot_data
                    else:
                        return f"data:image/png;base64,{screenshot_data}"
            return ''
        except Exception as e:
            print(f"Error taking screenshot: {e}")
            return ''

    async def _get_page_html(self, browser_session: BrowserSession) -> str:
        """Get page HTML content."""
        try:
            return browser_session.get_page_html() or ''
        except Exception as e:
            print(f"Error getting page HTML: {e}")
            return ''

    async def _get_page_structure(self, browser_session: BrowserSession) -> Dict[str, Any]:
        """Get page structure information including DOM and accessibility tree."""
        try:
            # Get page structure from Browser-Use
            structure = browser_session.get_page_structure()

            # Convert to OpenHands format
            result = {
                'dom': {},
                'axtree': {},
                'properties': {},
            }

            if structure:
                # Browser-Use structure might be different from BrowserGym
                # We'll need to adapt it to match the expected format
                result['dom'] = structure.get('dom', {})
                result['axtree'] = structure.get('accessibility', {})
                result['properties'] = structure.get('properties', {})

            return result

        except Exception as e:
            print(f"Error getting page structure: {e}")
            return {'dom': {}, 'axtree': {}, 'properties': {}}

    def get_agent_obs_text(self, observation: BrowserOutputObservation) -> str:
        """Get agent observation text in the same format as the original implementation."""
        if observation.trigger_by_action == 'browse_interactive':
            text = f'[Current URL: {observation.url}]\n'
            text += f'[Focused element bid: {observation.focused_element_bid}]\n'

            # Add screenshot path information if available
            if observation.screenshot_path:
                text += f'[Screenshot saved to: {observation.screenshot_path}]\n'

            text += '\n'

            if observation.error:
                text += (
                    '================ BEGIN error message ===============\n'
                    'The following error occurred when executing the last action:\n'
                    f'{observation.last_browser_action_error}\n'
                    '================ END error message ===============\n'
                )
            else:
                text += '[Action executed successfully.]\n'

            # Add accessibility tree if available
            if observation.axtree_object:
                try:
                    axtree_text = self._flatten_axtree_to_str(
                        observation.axtree_object,
                        observation.extra_element_properties,
                        filter_visible_only=observation.filter_visible_only,
                    )
                    text += (
                        f'Accessibility tree of the webpage:\n'
                        f'Note: [bid] is the unique alpha-numeric identifier at the beginning of lines for each element in the AXTree. Always use bid to refer to elements in your actions.\n'
                        f'============== BEGIN accessibility tree ==============\n'
                        f'{axtree_text}\n'
                        f'============== END accessibility tree ==============\n'
                    )
                except Exception as e:
                    text += f'\n[Error encountered when processing the accessibility tree: {e}]'

            return text

        elif observation.trigger_by_action == 'browse':
            text = f'[Current URL: {observation.url}]\n'

            if observation.error:
                text += (
                    '================ BEGIN error message ===============\n'
                    'The following error occurred when trying to visit the URL:\n'
                    f'{observation.last_browser_action_error}\n'
                    '================ END error message ===============\n'
                )
            text += '============== BEGIN webpage content ==============\n'
            text += observation.content
            text += '\n============== END webpage content ==============\n'
            return text
        else:
            raise ValueError(f'Invalid trigger_by_action: {observation.trigger_by_action}')

    def _flatten_axtree_to_str(
        self,
        axtree_object: Dict[str, Any],
        extra_properties: Dict[str, Any],
        filter_visible_only: bool = False,
    ) -> str:
        """
        Flatten accessibility tree to string format.

        This is a simplified implementation. In a real scenario, you'd want to
        implement proper accessibility tree flattening similar to BrowserGym.
        """
        # Simplified implementation - in practice, you'd want to implement
        # proper accessibility tree traversal and formatting
        result = []

        def traverse_node(node, level=0):
            if not isinstance(node, dict):
                return

            # Extract basic information
            bid = node.get('bid', '')
            tag = node.get('tag', '')
            text = node.get('text', '')
            visible = node.get('visible', True)

            # Skip invisible elements if filtering
            if filter_visible_only and not visible:
                return

            # Format the line
            indent = '  ' * level
            line = f'{indent}[{bid}] {tag}'
            if text:
                line += f': {text[:100]}'  # Truncate long text
            result.append(line)

            # Traverse children
            children = node.get('children', [])
            for child in children:
                traverse_node(child, level + 1)

        # Start traversal from root
        if isinstance(axtree_object, dict):
            traverse_node(axtree_object)

        return '\n'.join(result)
