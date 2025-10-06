"""Tests for argparser modules using pytest."""

import argparse
import pytest

from openhands_cli.argparsers.cli_parser import add_cli_parser
from openhands_cli.argparsers.main_parser import create_main_parser
from openhands_cli.argparsers.serve_parser import add_serve_parser


def test_create_main_parser():
    parser = create_main_parser()
    assert isinstance(parser, argparse.ArgumentParser)
    assert parser.description == "OpenHands CLI - Terminal User Interface for OpenHands AI Agent"


def test_main_parser_help_contains_expected_sections():
    parser = create_main_parser()
    help_text = parser.format_help()
    assert "cli" in help_text
    assert "serve" in help_text
    assert "terminal interface" in help_text
    assert "web interface" in help_text


@pytest.mark.parametrize(
    "args,resume",
    [
        (["cli"], None),
        (["cli", "--resume", "test-id"], "test-id"),
    ],
)
def test_cli_subcommand_parsing(args, resume):
    parser = create_main_parser()
    parsed = parser.parse_args(args)
    assert parsed.command == "cli"
    assert parsed.resume == resume


@pytest.mark.parametrize(
    "args,mount_cwd,gpu",
    [
        (["serve"], False, False),
        (["serve", "--mount-cwd"], True, False),
        (["serve", "--gpu"], False, True),
        (["serve", "--mount-cwd", "--gpu"], True, True),
    ],
)
def test_serve_subcommand_parsing(args, mount_cwd, gpu):
    parser = create_main_parser()
    parsed = parser.parse_args(args)
    assert parsed.command == "serve"
    assert parsed.mount_cwd == mount_cwd
    assert parsed.gpu == gpu


def test_no_subcommand_defaults():
    parser = create_main_parser()
    parsed = parser.parse_args([])
    assert parsed.command is None


def test_add_cli_parser():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    cli_parser = add_cli_parser(subparsers)

    assert isinstance(cli_parser, argparse.ArgumentParser)

    parsed = parser.parse_args(["cli", "--resume", "test"])
    assert parsed.resume == "test"


def test_add_serve_parser():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    serve_parser = add_serve_parser(subparsers)

    assert isinstance(serve_parser, argparse.ArgumentParser)

    parsed = parser.parse_args(["serve", "--mount-cwd", "--gpu"])
    assert parsed.mount_cwd
    assert parsed.gpu


def test_cli_parser_default_resume():
    parser = create_main_parser()
    parsed = parser.parse_args(["cli"])
    assert parsed.resume is None


def test_serve_parser_default_flags():
    parser = create_main_parser()
    parsed = parser.parse_args(["serve"])
    assert not parsed.mount_cwd
    assert not parsed.gpu
