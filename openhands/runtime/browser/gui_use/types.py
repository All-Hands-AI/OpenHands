from enum import StrEnum
from typing import Literal, TypedDict


class Resolution(TypedDict):
    width: int
    height: int


class ScalingSource(StrEnum):
    COMPUTER = 'computer'
    API = 'api'


ComputerUseAction = Literal[
    'type',  # type sequence                     --> keyboard_type
    'key',  # press a key or key comb            --> keyboard_press
    'mouse_move',  # move mouse to a position    --> mouse_move
    'left_click',  # left click                  --> mouse_click
    'left_click_drag',  # left click and drag    --> mouse_drag_and_drop
    'right_click',  # right click                --> mouse_click
    'middle_click',  # middle click              --> mouse_click
    'double_click',  # double left click         --> mouse_dblclick
    'screenshot',  # take a screenshot           --> noop
    'cursor_position',  # get cursor position    --> noop
]
