import pytest

from openhands.events.observation import BrowserOutputObservation
from openhands.runtime.browser.transformer import (
    translate_computer_use_action_to_browsergym_action,
)


@pytest.fixture
def last_obs():
    return BrowserOutputObservation(
        content='Hello, World!',
        url='https://example.com',
        screenshot='screenshot',
        mouse_position=[50, 100],
    )


def test_keyboard_type(last_obs):
    code = """type(text="Hello, World!")"""
    expected = "keyboard_type(key='Hello, World!')\n"
    assert (
        translate_computer_use_action_to_browsergym_action(code, last_obs) == expected
    )


def test_mouse_move(last_obs):
    code = """mouse_move(coordinate=(100, 200))"""
    expected = 'mouse_move(to_x=100, to_y=200, from_x=50, from_y=100)\n'
    assert (
        translate_computer_use_action_to_browsergym_action(code, last_obs) == expected
    )


def test_left_click(last_obs):
    code = """left_click()"""
    expected = "mouse_click(button='left', x=50, y=100)\n"
    assert (
        translate_computer_use_action_to_browsergym_action(code, last_obs) == expected
    )


def test_right_click(last_obs):
    code = """right_click()"""
    expected = "mouse_click(button='right', x=50, y=100)\n"
    assert (
        translate_computer_use_action_to_browsergym_action(code, last_obs) == expected
    )


def test_middle_click(last_obs):
    code = """middle_click()"""
    expected = "mouse_click(button='middle', x=50, y=100)\n"
    assert (
        translate_computer_use_action_to_browsergym_action(code, last_obs) == expected
    )


def test_double_click(last_obs):
    code = """double_click()"""
    expected = "mouse_dblclick(button='left', x=50, y=100)\n"
    assert (
        translate_computer_use_action_to_browsergym_action(code, last_obs) == expected
    )


def test_screenshot(last_obs):
    code = """screenshot()"""
    expected = 'noop()\n'
    assert (
        translate_computer_use_action_to_browsergym_action(code, last_obs) == expected
    )


def test_cursor_position(last_obs):
    code = """cursor_position()"""
    expected = 'noop()\n'
    assert (
        translate_computer_use_action_to_browsergym_action(code, last_obs) == expected
    )


def test_missing_mouse_position():
    last_obs = BrowserOutputObservation(
        content='Hello, World!',
        url='https://example.com',
        screenshot='screenshot',
        mouse_position=None,
    )
    code = """mouse_move(coordinate=(100, 200))"""
    expected = 'mouse_move(to_x=100, to_y=200, from_x=0, from_y=0)\n'
    assert (
        translate_computer_use_action_to_browsergym_action(code, last_obs) == expected
    )


def test_empty_mouse_position():
    last_obs = BrowserOutputObservation(
        content='Hello, World!',
        url='https://example.com',
        screenshot='screenshot',
        mouse_position=[],
    )
    code = """mouse_move(coordinate=(100, 200))"""
    expected = 'mouse_move(to_x=100, to_y=200, from_x=0, from_y=0)\n'
    assert (
        translate_computer_use_action_to_browsergym_action(code, last_obs) == expected
    )
