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
from openhands_cli.locations import WORKING_DIR, AGENT_SPEC_PATH


dummy_agent_specs = """{"llm":{"model":"litellm_proxy/claude-sonnet-4-20250514","api_key":"**********","base_url":null,"api_version":null,"aws_access_key_id":null,"aws_secret_access_key":null,"aws_region_name":null,"openrouter_site_url":"https://docs.all-hands.dev/","openrouter_app_name":"OpenHands","num_retries":5,"retry_multiplier":8.0,"retry_min_wait":8,"retry_max_wait":64,"timeout":null,"max_message_chars":30000,"temperature":0.0,"top_p":1.0,"top_k":null,"custom_llm_provider":null,"max_input_tokens":200000,"max_output_tokens":64000,"input_cost_per_token":null,"output_cost_per_token":null,"ollama_base_url":null,"drop_params":true,"modify_params":true,"disable_vision":null,"disable_stop_word":false,"caching_prompt":true,"log_completions":false,"log_completions_folder":"logs/completions","custom_tokenizer":null,"native_tool_calling":null,"reasoning_effort":"high","seed":null,"safety_settings":null,"service_id":"default","OVERRIDE_ON_SERIALIZE":["api_key","aws_access_key_id","aws_secret_access_key"]},"tools":[{"name":"BashTool","params":{"working_dir":"/Users/rohitmalhotra/.openhands"}},{"name":"FileEditorTool","params":{}},{"name":"TaskTrackerTool","params":{"save_dir":"/Users/rohitmalhotra/.openhands/.openhands"}},{"name":"BrowserToolSet","params":{}}],"mcp_config":{"mcpServers":{"fetch":{"command":"uvx","args":["mcp-server-fetch"]},"repomix":{"command":"npx","args":["-y","repomix@1.4.2","--mcp"]}}},"filter_tools_regex":"^(?!repomix)(.*)|^repomix.*pack_codebase.*$","agent_context":null,"system_prompt_filename":"system_prompt.j2","system_prompt_kwargs":{"cli_mode":true},"condenser":{"llm":{"model":"litellm_proxy/claude-sonnet-4-20250514","api_key":"**********","base_url":null,"api_version":null,"aws_access_key_id":null,"aws_secret_access_key":null,"aws_region_name":null,"openrouter_site_url":"https://docs.all-hands.dev/","openrouter_app_name":"OpenHands","num_retries":5,"retry_multiplier":8.0,"retry_min_wait":8,"retry_max_wait":64,"timeout":null,"max_message_chars":30000,"temperature":0.0,"top_p":1.0,"top_k":null,"custom_llm_provider":null,"max_input_tokens":200000,"max_output_tokens":64000,"input_cost_per_token":null,"output_cost_per_token":null,"ollama_base_url":null,"drop_params":true,"modify_params":true,"disable_vision":null,"disable_stop_word":false,"caching_prompt":true,"log_completions":false,"log_completions_folder":"logs/completions","custom_tokenizer":null,"native_tool_calling":null,"reasoning_effort":"high","seed":null,"safety_settings":null,"service_id":"default","OVERRIDE_ON_SERIALIZE":["api_key","aws_access_key_id","aws_secret_access_key"]},"max_size":80,"keep_first":4,"kind":"openhands.sdk.context.condenser.llm_summarizing_condenser.LLMSummarizingCondenser","_du_spec":null}}"""

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
    install_pyinstaller: bool = False,
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


def test_executable() -> bool:
    """Test the built executable with simplified checks."""
    print('🧪 Testing the built executable...')

    spec_path = os.path.join(WORKING_DIR, AGENT_SPEC_PATH)

    specs_path = Path(os.path.expanduser(spec_path))
    if specs_path.exists():
        print(f"⚠️  Using existing settings at {specs_path}")
    else:
        print(f"💾 Creating dummy settings at {specs_path}")
        specs_path.parent.mkdir(parents=True, exist_ok=True)
        specs_path.write_text(json.dumps(dummy_agent_specs))

    exe_path = Path('dist/openhands-cli')
    if not exe_path.exists():
        # Try with .exe extension for Windows
        exe_path = Path('dist/openhands-cli.exe')
        if not exe_path.exists():
            print('❌ Executable not found!')
            return False

    try:
        # Make executable on Unix-like systems
        if os.name != 'nt':
            os.chmod(exe_path, 0o755)

        # Simple test: Check that executable can start and respond to /help command
        print('  Testing executable startup and /help command...')
        input_script = "/help\n/exit\n" # Send /help command then exit
        result = subprocess.run(
            [str(exe_path)],
            capture_output=True,
            text=True,
            timeout=30,
            input=input_script,
            env={
                **os.environ
            },
        )

        # Check for expected help output
        output = result.stdout + result.stderr
        if 'OpenHands CLI Help' in output and 'Available commands:' in output:
            print('  ✅ Executable starts and /help command works correctly')
            return True
        else:
            print('  ❌ Expected help output not found')
            print('  Combined output:', output[:1000])
            return False

    except subprocess.TimeoutExpired:
        print('  ❌ Executable test timed out')
        return False
    except Exception as e:
        print(f'❌ Error testing executable: {e}')
        return False


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

    args = parser.parse_args()

    print('🚀 OpenHands CLI Build Script')
    print('=' * 40)

    # Check if spec file exists
    if not os.path.exists(args.spec):
        print(f"❌ Spec file '{args.spec}' not found!")
        return 1

    # Build the executable
    if not build_executable(
        args.spec, clean=not args.no_clean, install_pyinstaller=args.install_pyinstaller
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
