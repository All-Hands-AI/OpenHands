#!/usr/bin/env python3
"""
OpenHands integration test using gpt-5-codex.
This test verifies that gpt-5-codex works correctly within the OpenHands agent framework.
"""

import os
import sys
import tempfile
from pathlib import Path

# Add the OpenHands directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from openhands.core.config import AppConfig, LLMConfig
from openhands.core.main import create_runtime, run_controller
from openhands.events.action import MessageAction
from openhands.events.observation import AgentFinishObservation


def test_openhands_with_gpt5_codex():
    """Test OpenHands agent with gpt-5-codex on a simple coding task."""
    print("🧪 Testing OpenHands with gpt-5-codex...")
    
    # Check if API key is available
    api_key = os.getenv('LLM_API_KEY') or os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ No API key found. Set LLM_API_KEY or OPENAI_API_KEY environment variable.")
        return False
    
    # Create a temporary workspace
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_dir = Path(temp_dir)
        
        # Configure OpenHands with gpt-5-codex
        config = AppConfig(
            workspace_base=str(workspace_dir),
            llm=LLMConfig(
                model='gpt-5-codex',
                api_key=api_key,
                base_url=os.getenv('LLM_BASE_URL'),
            ),
            runtime='local',
            max_iterations=10,
        )
        
        print(f"✅ Configured OpenHands with gpt-5-codex")
        print(f"📁 Workspace: {workspace_dir}")
        
        try:
            # Create runtime
            runtime = create_runtime(config)
            print("✅ Runtime created successfully")
            
            # Define a simple coding task
            task = """Create a Python file called 'calculator.py' that contains a simple Calculator class with methods for add, subtract, multiply, and divide. Include basic error handling for division by zero."""
            
            print(f"📋 Task: {task}")
            
            # Create initial message action
            action = MessageAction(content=task)
            
            # Run the controller
            print("🔄 Running OpenHands controller with gpt-5-codex...")
            state = run_controller(
                config=config,
                initial_user_action=action,
                runtime=runtime,
                fake_user_response_fn=lambda _: "LGTM!",  # Auto-approve any user prompts
            )
            
            print("✅ Controller execution completed")
            
            # Check if the task was completed successfully
            if state.history:
                last_event = state.history[-1]
                if isinstance(last_event, AgentFinishObservation):
                    print("✅ Agent finished successfully")
                    
                    # Check if the calculator.py file was created
                    calculator_file = workspace_dir / 'calculator.py'
                    if calculator_file.exists():
                        print("✅ calculator.py file was created")
                        
                        # Read and verify the content
                        content = calculator_file.read_text()
                        if 'class Calculator' in content and 'def add' in content:
                            print("✅ Calculator class with methods found")
                            print(f"📄 File size: {len(content)} characters")
                            return True
                        else:
                            print("❌ Calculator class or methods not found in file")
                            print(f"📄 File content preview: {content[:300]}...")
                    else:
                        print("❌ calculator.py file was not created")
                else:
                    print(f"⚠️  Agent did not finish normally. Last event: {type(last_event).__name__}")
            else:
                print("❌ No events in history")
            
            return False
            
        except Exception as e:
            print(f"❌ OpenHands execution failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            # Clean up runtime
            if 'runtime' in locals():
                try:
                    runtime.close()
                    print("✅ Runtime closed")
                except Exception as e:
                    print(f"⚠️  Error closing runtime: {e}")


if __name__ == '__main__':
    print("=" * 60)
    print("🧪 OPENHANDS GPT-5-CODEX INTEGRATION TEST")
    print("=" * 60)
    print("This test runs a real OpenHands task using gpt-5-codex")
    print("Make sure you have a valid API key set in LLM_API_KEY or OPENAI_API_KEY")
    print()
    
    try:
        if test_openhands_with_gpt5_codex():
            print("\n🎉 OPENHANDS INTEGRATION TEST PASSED!")
            print("✅ gpt-5-codex works correctly with OpenHands!")
            print("✅ Agent successfully completed a coding task!")
            print("\n🚀 Ready for production use!")
            sys.exit(0)
        else:
            print("\n❌ OPENHANDS INTEGRATION TEST FAILED!")
            print("Please check the logs above for details.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)