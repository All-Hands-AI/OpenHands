#!/usr/bin/env python3
"""
WebArena Evaluation Script

This script evaluates WebArena task results using the official WebArena evaluation harness
with BrowserGym state capture. It loads saved browser state and creates mock objects
that provide the exact state WebArena evaluators need.

This approach leverages BrowserGym's existing observation functions (extract_dom_snapshot, etc.)
which already provide WebArena-compatible state capture.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add WebArena to path
sys.path.insert(0, '/workspace/project/webarena')

def convert_openhands_trajectory_to_webarena_format(instance_data: Dict[str, Any]) -> List[Any]:
    """
    Convert OpenHands trajectory format to WebArena trajectory format.
    
    WebArena expects a list of alternating Action and StateInfo objects.
    OpenHands provides action/observation pairs in text format.
    """
    trajectory = []
    
    # Get the conversation history
    history = instance_data.get('history', [])
    
    for entry in history:
        if entry.get('source') == 'agent':
            # This is an agent action
            content = entry.get('message', {}).get('content', '')
            
            # Create a WebArena-compatible action
            action = {
                'action_type': 'browser_action',
                'content': content,
                'timestamp': entry.get('timestamp', 0)
            }
            trajectory.append(action)
        
        elif entry.get('source') == 'user':
            # This might be an observation or state info
            content = entry.get('message', {}).get('content', '')
            
            # Create a WebArena-compatible state info
            state_info = {
                'observation': content,
                'timestamp': entry.get('timestamp', 0)
            }
            trajectory.append(state_info)
    
    # Add a final stop action if needed
    if trajectory and not trajectory[-1].get('action_type'):
        trajectory.append({
            'action_type': 'stop',
            'content': 'Task completed',
            'timestamp': trajectory[-1].get('timestamp', 0) + 1
        })
    
    return trajectory


def evaluate_with_browsergym_state_capture(instance_data: Dict[str, Any], config_file: str) -> float:
    """
    Evaluate using official WebArena harness with BrowserGym state capture.
    
    This loads the saved browser state captured during inference and creates
    mock Page/CDPSession objects that provide the exact state WebArena evaluators need.
    """
    try:
        # Import BrowserGym state capture
        from browsergym_state_capture import (
            BrowserGymStateCapture, 
            MockPageForWebArena, 
            MockCDPSessionForWebArena
        )
        
        # Import WebArena evaluation components
        from evaluation_harness import evaluator_router
        
        # Load saved browser state
        instance_id = instance_data.get('instance_id', 'unknown')
        state_capture = BrowserGymStateCapture()
        
        try:
            saved_state = state_capture.load_state(instance_id)
            print(f"   ✅ Loaded browser state for {instance_id}")
        except FileNotFoundError:
            print(f"   ❌ No saved browser state found for {instance_id}")
            print(f"      Make sure inference was run with browser_logging_dir enabled")
            return 0.0
        
        # Create mock objects with saved state
        mock_page = MockPageForWebArena(saved_state)
        mock_client = MockCDPSessionForWebArena(saved_state)
        
        # Convert trajectory format
        trajectory = convert_openhands_trajectory_to_webarena_format(instance_data)
        
        # Get the official evaluator
        evaluator = evaluator_router(config_file)
        
        # Run evaluation with mock objects containing saved browser state
        score = evaluator(
            trajectory=trajectory,
            config_file=config_file,
            page=mock_page,        # Mock page with BrowserGym's captured state
            client=mock_client,    # Mock CDP session with BrowserGym's captured state
        )
        
        return score
        
    except ImportError as e:
        print(f"   ❌ Could not import BrowserGym state capture: {e}")
        print(f"      Make sure browsergym_state_capture.py is available")
        return 0.0
    except Exception as e:
        print(f"   ❌ Evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        return 0.0


def main():
    """Main evaluation function."""
    if len(sys.argv) != 2:
        print("Usage: python eval_infer.py <output_file>")
        sys.exit(1)
    
    output_file = sys.argv[1]
    
    if not os.path.exists(output_file):
        print(f"❌ Output file not found: {output_file}")
        sys.exit(1)
    
    print("🔍 WebArena Evaluation (BrowserGym State Capture)")
    print("=" * 60)
    
    # Load results
    with open(output_file, 'r') as f:
        results = [json.loads(line) for line in f]
    
    print(f"📊 Evaluating {len(results)} WebArena tasks...")
    
    # WebArena config files
    config_dir = Path('/workspace/project/webarena/config_files/examples')
    
    total_score = 0
    evaluated_count = 0
    
    for result in results:
        instance_id = result.get('instance_id', 'unknown')
        
        # Find corresponding config file
        config_file = config_dir / f"{instance_id}.json"
        
        if not config_file.exists():
            print(f"⚠️  Config file not found for {instance_id}")
            continue
        
        print(f"\n🧪 Evaluating {instance_id}...")
        
        try:
            # Use official WebArena evaluation with BrowserGym state capture
            score = evaluate_with_browsergym_state_capture(result, str(config_file))
            
            print(f"   Score: {score}")
            total_score += score
            evaluated_count += 1
            
        except Exception as e:
            print(f"   ❌ Evaluation failed: {e}")
    
    if evaluated_count > 0:
        average_score = total_score / evaluated_count
        print(f"\n📈 Results Summary:")
        print(f"   Tasks evaluated: {evaluated_count}")
        print(f"   Total score: {total_score}")
        print(f"   Average score: {average_score:.3f}")
        print(f"   Pass rate: {total_score}/{evaluated_count} ({100*total_score/evaluated_count:.1f}%)")
    else:
        print(f"\n❌ No tasks could be evaluated")
    
    print(f"\n🎯 Evaluation Method:")
    print(f"   - Uses official WebArena evaluation harness")
    print(f"   - Loads browser state captured by BrowserGym during inference")
    print(f"   - Creates mock Page/CDPSession objects with exact browser state")
    print(f"   - WebArena evaluators get the exact state they need")
    
    print(f"\n💡 To enable browser state capture during inference:")
    print(f"   export WEBARENA_BROWSER_LOGGING_DIR=/tmp/webarena_states")


if __name__ == "__main__":
    main()