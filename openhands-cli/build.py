#!/usr/bin/env python3
"""
Build script for OpenHands CLI using PyInstaller.

This script packages the OpenHands CLI into a standalone executable binary
using PyInstaller with the custom spec file.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
import time
from openhands_cli.locations import LLM_SETTINGS_PATH
import select

WELCOME_MARKERS = ["welcome", "openhands cli", "type /help", "available commands", ">"]

dummy_settings = {
    "model": "litellm_proxy/claude-sonnet-4-20250514",
    "api_key": "adfadf",
    "base_url": "https://llm-proxy.app.all-hands.dev/",
    "num_retries": 5,
    "retry_multiplier": 8,
    "retry_min_wait": 8,
    "retry_max_wait": 64,
    "max_message_chars": 30000,
    "temperature": 0.0,
    "top_p": 1.0,
    "max_input_tokens": 200000,
    "max_output_tokens": 64000,
    "drop_params": True,
    "modify_params": True,
    "disable_stop_word": False,
    "caching_prompt": True,
    "log_completions": False,
    "log_completions_folder": "logs/completions",
    "reasoning_effort": "high",
    "service_id": "default",
    "OVERRIDE_ON_SERIALIZE": ["api_key", "aws_access_key_id", "aws_secret_access_key"],
}


# =================================================
# SECTION: Build Binary
# =================================================



def clean_build_directories() -> None:
    """Clean up previous build artifacts."""
    print('🧹 Cleaning up previous build artifacts...')

    build_dirs = ['build', 'dist', '__pycache__']
    for dir_name in build_dirs:
        if os.path.exists(dir_name):
            print(f'  Removing {dir_name}/')
            shutil.rmtree(dir_name)

    # Clean up .pyc files
    for root, _dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.pyc'):
                os.remove(os.path.join(root, file))

    print('✅ Cleanup complete!')


def check_pyinstaller() -> bool:
    """Check if PyInstaller is available."""
    try:
        subprocess.run(
            ['uv', 'run', 'pyinstaller', '--version'], check=True, capture_output=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(
            '❌ PyInstaller is not available. Use --install-pyinstaller flag or install manually with:'
        )
        print('   uv add --dev pyinstaller')
        return False

def build_executable(
    spec_file: str = 'openhands-cli.spec',
    clean: bool = True,
) -> bool:
    """Build the executable using PyInstaller."""
    if clean:
        clean_build_directories()

    # Check if PyInstaller is available (installation is handled by build.sh)
    if not check_pyinstaller():
        return False

    print(f'🔨 Building executable using {spec_file}...')

    try:
        # Run PyInstaller with uv
        cmd = ['uv', 'run', 'pyinstaller', spec_file, '--clean']

        print(f'Running: {" ".join(cmd)}')
        subprocess.run(cmd, check=True, capture_output=True, text=True)

        print('✅ Build completed successfully!')

        # Check if the executable was created
        dist_dir = Path('dist')
        if dist_dir.exists():
            executables = list(dist_dir.glob('*'))
            if executables:
                print('📁 Executable(s) created in dist/:')
                for exe in executables:
                    size = exe.stat().st_size / (1024 * 1024)  # Size in MB
                    print(f'  - {exe.name} ({size:.1f} MB)')
            else:
                print('⚠️  No executables found in dist/ directory')

        return True

    except subprocess.CalledProcessError as e:
        print(f'❌ Build failed: {e}')
        if e.stdout:
            print('STDOUT:', e.stdout)
        if e.stderr:
            print('STDERR:', e.stderr)
        return False


# =================================================
# SECTION: Test and profile binary
# =================================================


def _is_welcome(line: str) -> bool:
    s = line.strip().lower()
    return any(marker in s for marker in WELCOME_MARKERS)

def test_executable() -> bool:
    """Test the built executable, measuring boot time and total test time."""
    print('🧪 Testing the built executable...')

    settings_path = Path(LLM_SETTINGS_PATH)
    if not settings_path.exists():
        print(f"💾 Creating dummy settings at {settings_path}")
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(json.dumps(dummy_settings))

    exe_path = Path('dist/openhands-cli')
    if not exe_path.exists():
        exe_path = Path('dist/openhands-cli.exe')
        if not exe_path.exists():
            print('❌ Executable not found!')
            return False

    try:
        if os.name != 'nt':
            os.chmod(exe_path, 0o755)

        boot_start = time.time()
        proc = subprocess.Popen(
            [str(exe_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env={**os.environ},
        )

        # --- Wait for welcome ---
        deadline = boot_start + 30
        saw_welcome = False
        captured = []

        while time.time() < deadline:
            if proc.poll() is not None:
                break
            rlist, _, _ = select.select([proc.stdout], [], [], 0.2)
            if not rlist:
                continue
            line = proc.stdout.readline()
            if not line:
                continue
            captured.append(line)
            if _is_welcome(line):
                saw_welcome = True
                break

        if not saw_welcome:
            print("❌ Did not detect welcome prompt")
            try: proc.kill()
            except Exception: pass
            return False

        boot_end = time.time()
        print(f"⏱️  Boot to welcome: {boot_end - boot_start:.2f} seconds")

        # --- Run /help then /exit ---
        if proc.stdin is None:
            print("❌ stdin unavailable")
            proc.kill()
            return False

        proc.stdin.write("/help\n/exit\n")
        proc.stdin.flush()
        out, _ = proc.communicate(timeout=20)

        total_end = time.time()
        full_output = ''.join(captured) + (out or '')

        print(f"⏱️  End-to-end test time: {total_end - boot_start:.2f} seconds")

        if "available commands" in full_output.lower():
            print("✅ Executable starts, welcome detected, and /help works")
            return True
        else:
            print("❌ /help output not found")
            print("Output preview:", full_output[-500:])
            return False

    except subprocess.TimeoutExpired:
        print("❌ Executable test timed out")
        try: proc.kill()
        except Exception: pass
        return False
    except Exception as e:
        print(f"❌ Error testing executable: {e}")
        try: proc.kill()
        except Exception: pass
        return False



# =================================================
# SECTION: Main
# =================================================


def main() -> int:
    """Main function."""
    parser = argparse.ArgumentParser(description='Build OpenHands CLI executable')
    parser.add_argument(
        '--spec', default='openhands-cli.spec', help='PyInstaller spec file to use'
    )
    parser.add_argument(
        '--no-clean', action='store_true', help='Skip cleaning build directories'
    )
    parser.add_argument(
        '--no-test', action='store_true', help='Skip testing the built executable'
    )
    parser.add_argument(
        '--install-pyinstaller',
        action='store_true',
        help='Install PyInstaller using uv before building',
    )

    parser.add_argument(
        '--no-build', action='store_true', help='Skip testing the built executable'
    )

    args = parser.parse_args()

    print('🚀 OpenHands CLI Build Script')
    print('=' * 40)

    # Check if spec file exists
    if not os.path.exists(args.spec):
        print(f"❌ Spec file '{args.spec}' not found!")
        return 1

    # Build the executable
    if not args.no_build and not build_executable(
        args.spec, clean=not args.no_clean
    ):
        return 1

    # Test the executable
    if not args.no_test:
        if not test_executable():
            print('❌ Executable test failed, build process failed')
            return 1

    print('\n🎉 Build process completed!')
    print("📁 Check the 'dist/' directory for your executable")

    return 0




if __name__ == '__main__':
    sys.exit(main())
