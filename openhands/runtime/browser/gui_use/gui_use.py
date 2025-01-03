import base64
from pathlib import Path
from uuid import uuid4

from openhands_aci.editor.exceptions import ToolError
from openhands_aci.utils.shell import run_shell_cmd

from openhands.runtime.browser.gui_use.types import (
    MAX_SCALING_TARGETS,
    OUTPUT_DIR,
    ScalingSource,
)
from openhands.runtime.browser.gui_use.types import ComputerUseAction as Action


class GUIUseTool:
    """
    A tool that allows the agent to interact with the screen, keyboard, and mouse of the current computer.
    The tool parameters are defined by Anthropic and are not editable.

    Original implementation: https://github.com/anthropics/anthropic-quickstarts/blob/main/computer-use-demo/computer_use_demo/tools/computer.py
    """

    TOOL_NAME = 'gui_use'
    _scaling_enabled = True

    width: int  # Screen width
    height: int  # Screen height

    def __init__(self):
        # self.width = int(os.getenv('WIDTH') or 0)
        # self.height = int(os.getenv('HEIGHT') or 0)
        self.width = 1280
        self.height = 720
        assert self.width and self.height, 'WIDTH, HEIGHT must be set'

    def validate_and_transform_args(
        self,
        *,
        action: Action,
        text: str | None = None,
        coordinate: list[int] | None = None,
        **kwargs,
    ) -> dict[str, str | tuple[int, int] | None]:
        if action in ('mouse_move', 'left_click_drag'):
            if coordinate is None:
                raise ToolError(f'coordinate is required for {action}')
            if text is not None:
                raise ToolError(f'text is not accepted for {action}')
            if not isinstance(coordinate, list) or len(coordinate) != 2:
                raise ToolError(f'{coordinate} must be a tuple of length 2')
            if not all(isinstance(i, int) and i >= 0 for i in coordinate):
                raise ToolError(f'{coordinate} must be a tuple of non-negative ints')

            x, y = self.scale_coordinates(
                ScalingSource.API, coordinate[0], coordinate[1]
            )

            return {
                'action': action,
                'coordinate': (x, y),
                'text': text,
            }

        if action in ('key', 'type', 'goto'):
            if text is None:
                raise ToolError(f'text is required for {action}')
            if coordinate is not None:
                raise ToolError(f'coordinate is not accepted for {action}')
            if not isinstance(text, str):
                raise ToolError(output=f'{text} must be a string')

            return {
                'action': action,
                'coordinate': coordinate,
                'text': text,
            }

        if action in (
            'left_click',
            'right_click',
            'double_click',
            'middle_click',
            'screenshot',
            'cursor_position',
        ):
            if text is not None:
                raise ToolError(f'text is not accepted for {action}')
            if coordinate is not None:
                raise ToolError(f'coordinate is not accepted for {action}')

            return {
                'action': action,
                'coordinate': coordinate,
                'text': text,
            }

        raise ToolError(f'Invalid action: {action}')

    def scale_coordinates(
        self, source: ScalingSource, x: int, y: int
    ) -> tuple[int, int]:
        """Scale coordinates to a target maximum resolution."""
        if not self._scaling_enabled:
            return x, y
        ratio = self.width / self.height
        target_dimension = None
        for dimension in MAX_SCALING_TARGETS.values():
            # allow some error in the aspect ratio - not ratios are exactly 16:9
            if abs(dimension['width'] / dimension['height'] - ratio) < 0.02:
                if dimension['width'] < self.width:
                    target_dimension = dimension
                break
        if target_dimension is None:
            return x, y
        # should be less than 1
        x_scaling_factor = target_dimension['width'] / self.width
        y_scaling_factor = target_dimension['height'] / self.height
        if source == ScalingSource.API:
            if x > self.width or y > self.height:
                raise ToolError(f'Coordinates {x}, {y} are out of bounds')
            # scale up
            return round(x / x_scaling_factor), round(y / y_scaling_factor)
        # scale down
        return round(x * x_scaling_factor), round(y * y_scaling_factor)

    def resize_image(self, base64_image: str) -> str:
        data_prefix = 'data:image/png;base64,'
        if base64_image.startswith('data:image/png;base64,'):
            base64_image = base64_image[len(data_prefix) :]

        output_dir = Path(OUTPUT_DIR)
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f'screenshot_{uuid4().hex}.png'

        # Write the base64 image to a file
        with open(path, 'wb') as f:
            f.write(base64.b64decode(base64_image))

        if self._scaling_enabled:
            x, y = self.scale_coordinates(
                ScalingSource.COMPUTER, self.width, self.height
            )
            # Resize the image
            run_shell_cmd(f'convert {path} -resize {x}x{y}! {path}')

        if path.exists():
            return data_prefix + base64.b64encode(path.read_bytes()).decode()

        raise ToolError(f'Failed to resize image: {path}')
