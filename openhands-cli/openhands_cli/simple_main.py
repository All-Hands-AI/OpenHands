#!/usr/bin/env python3
"""
Simple main entry point for OpenHands CLI.
This module provides a streamlined interface using the optimized agent_chat module.
"""

import os
import sys
import threading
import time
import gc
from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import HTML


def cleanup_resources():
    """Attempt graceful cleanup with fallback to force exit."""
    try:
        gc.collect()
        time.sleep(0.1)
        
        daemon_threads = [t for t in threading.enumerate() 
                         if t != threading.current_thread() and t.daemon and t.is_alive()]
        
        if daemon_threads:
            time.sleep(0.2)
            daemon_threads = [t for t in threading.enumerate() 
                             if t != threading.current_thread() and t.daemon and t.is_alive()]
            if daemon_threads:
                print(f"Warning: {len(daemon_threads)} daemon threads still running:", 
                      [t.name for t in daemon_threads], file=sys.stderr)
                
        os._exit(0)
    except Exception as e:
        print(f"Cleanup error: {e}", file=sys.stderr)
        os._exit(1)


def main() -> None:
    """Main entry point with cleanup handling."""
    
    # Set up cleanup timer
    cleanup_timer = threading.Timer(0.1, cleanup_resources)
    cleanup_timer.daemon = True
    
    try:
        # Use the optimized run_cli_entry function
        from openhands_cli.agent_chat import run_cli_entry
        run_cli_entry()
    except EOFError:
        print_formatted_text(HTML("\n<yellow>Goodbye! 👋</yellow>"))
    except Exception as e:
        print_formatted_text(HTML(f"<red>Error starting agent chat: {e}</red>"))
        import traceback
        traceback.print_exc()
        raise
    finally:
        cleanup_timer.start()


if __name__ == "__main__":
    main()