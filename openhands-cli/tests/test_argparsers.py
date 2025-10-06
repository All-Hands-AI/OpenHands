"""Tests for argparser modules."""

import argparse
import unittest

from openhands_cli.argparsers.cli_parser import add_cli_parser
from openhands_cli.argparsers.main_parser import create_main_parser
from openhands_cli.argparsers.serve_parser import add_serve_parser


class TestArgParsers(unittest.TestCase):
    """Test cases for argument parsers."""

    def test_create_main_parser(self):
        """Test main parser creation."""
        parser = create_main_parser()
        self.assertIsInstance(parser, argparse.ArgumentParser)
        self.assertEqual(parser.description, 'OpenHands CLI - Terminal User Interface for OpenHands AI Agent')

    def test_main_parser_help(self):
        """Test main parser help output."""
        parser = create_main_parser()
        help_text = parser.format_help()
        self.assertIn('cli', help_text)
        self.assertIn('serve', help_text)
        self.assertIn('terminal interface', help_text)
        self.assertIn('web interface', help_text)

    def test_cli_subcommand_parsing(self):
        """Test CLI subcommand parsing."""
        parser = create_main_parser()
        
        # Test basic cli command
        args = parser.parse_args(['cli'])
        self.assertEqual(args.command, 'cli')
        self.assertIsNone(args.resume)
        
        # Test cli with resume
        args = parser.parse_args(['cli', '--resume', 'test-id'])
        self.assertEqual(args.command, 'cli')
        self.assertEqual(args.resume, 'test-id')

    def test_serve_subcommand_parsing(self):
        """Test serve subcommand parsing."""
        parser = create_main_parser()
        
        # Test basic serve command
        args = parser.parse_args(['serve'])
        self.assertEqual(args.command, 'serve')
        self.assertFalse(args.mount_cwd)
        self.assertFalse(args.gpu)
        
        # Test serve with mount-cwd
        args = parser.parse_args(['serve', '--mount-cwd'])
        self.assertEqual(args.command, 'serve')
        self.assertTrue(args.mount_cwd)
        self.assertFalse(args.gpu)
        
        # Test serve with gpu
        args = parser.parse_args(['serve', '--gpu'])
        self.assertEqual(args.command, 'serve')
        self.assertFalse(args.mount_cwd)
        self.assertTrue(args.gpu)
        
        # Test serve with both options
        args = parser.parse_args(['serve', '--mount-cwd', '--gpu'])
        self.assertEqual(args.command, 'serve')
        self.assertTrue(args.mount_cwd)
        self.assertTrue(args.gpu)

    def test_no_subcommand(self):
        """Test behavior when no subcommand is provided."""
        parser = create_main_parser()
        args = parser.parse_args([])
        self.assertIsNone(args.command)

    def test_add_cli_parser(self):
        """Test add_cli_parser function."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        
        cli_parser = add_cli_parser(subparsers)
        self.assertIsInstance(cli_parser, argparse.ArgumentParser)
        
        # Test that the parser was added to subparsers
        args = parser.parse_args(['cli', '--resume', 'test'])
        self.assertEqual(args.resume, 'test')

    def test_add_serve_parser(self):
        """Test add_serve_parser function."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        
        serve_parser = add_serve_parser(subparsers)
        self.assertIsInstance(serve_parser, argparse.ArgumentParser)
        
        # Test that the parser was added to subparsers
        args = parser.parse_args(['serve', '--mount-cwd', '--gpu'])
        self.assertTrue(args.mount_cwd)
        self.assertTrue(args.gpu)

    def test_cli_parser_defaults(self):
        """Test CLI parser default values."""
        parser = create_main_parser()
        args = parser.parse_args(['cli'])
        self.assertIsNone(args.resume)

    def test_serve_parser_defaults(self):
        """Test serve parser default values."""
        parser = create_main_parser()
        args = parser.parse_args(['serve'])
        self.assertFalse(args.mount_cwd)
        self.assertFalse(args.gpu)


if __name__ == '__main__':
    unittest.main()